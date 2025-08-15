import os
import re
import markdown
import mysql.connector
import time
import jwt
import libsql
import sqlite3
from typing import List, Dict
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def encode_jwt(key):
    time_ = 86400  # 24 hours
    claims = {"a": "rw", "iat": int(time.time()), "exp": int(time.time()) + time_}
    return jwt.encode(claims, key, algorithm="EdDSA")


def get_sqlite_connection(db_path):
    """
    Get a SQLite/libsql connection that automatically handles libsql if configured.
    Falls back to regular SQLite if LIBSQL_URL is not set.
    """
    libsql_url = os.getenv("LIBSQL_CONNECTION_URL")

    if libsql_url:
        # Read the private key for auth
        key_path = Path(__file__).parent / "certs" / "private_key.pem"
        with open(key_path, "r") as f:
            private_key = f.read()

        auth_token = encode_jwt(private_key)
        conn = libsql.connect(libsql_url, auth_token=auth_token)
    else:
        # Fallback to regular SQLite
        conn = sqlite3.connect(db_path)

    return conn


def get_mysql_connection():
    """Create and return a MySQL connection."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=os.getenv("MYSQL_PORT"),
        user=os.getenv("MYSQL_USERNAME"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8mb4",
        use_unicode=True,
        buffered=True,
    )


def clean_content(content: str) -> str:
    """Clean and format content."""
    content = content.replace(r"\*", "*")
    content = re.sub("&amp;", "&", content)
    content = re.sub(r"\n+", "\n\n", content)
    content = re.sub(r"\n#", "\n\n#", content).replace("* ###", "###")
    content = re.sub(r"(?<=[;:]\s)(\d+[).])", r"\n\1", content)
    content = re.sub(
        """tags: 

    nan""",
        "tags:",
        content,
    )
    content = content.replace("LINEBREAK", "<br>").replace("HBREAK", "<hr>")
    return content


def combine_search_gens_to_article(title=None, introduction=None, sections=None):
    output = ""

    if title:
        output += f"# {title}\n\n"

    if introduction:
        output += f"{introduction}\n\n"

    counter = 0
    for section in sections:
        if not section.get("content"):
            break
        counter += 1
        output += f"## {section['title']}\n\n"
        output += section["content"] + "\n\n"

    return output


def get_mysql_gen_data(
    mysql_conn,
    module_id: int,
    identifiers: List[str],
    type_: str = "boxer",
    use_citations: bool = False,
) -> List[Dict]:
    """Get and process generation data from MySQL."""
    cursor = mysql_conn.cursor(dictionary=True, buffered=True)

    query = """
        SELECT
            pmsm.id,
            pmsm.one_liner,
            pmsm.excerpt,
            pmsm.introduction,
            pmsm.identifier
        FROM projects_modules_search_map AS pmsm
        WHERE pmsm.module_id = %s
          AND pmsm.`type` = %s
          AND pmsm.introduction IS NOT NULL
          AND pmsm.one_liner IS NOT NULL
          AND pmsm.excerpt IS NOT NULL
    """
    params = [module_id, type_]

    if identifiers:
        # De-dupe while preserving order
        seen = set()
        identifiers = [x for x in identifiers if not (x in seen or seen.add(x))]

        placeholders = ", ".join(["%s"] * len(identifiers))
        query += f" AND pmsm.identifier IN ({placeholders})"
        params.extend(identifiers)

    cursor.execute(query, params)

    search_results = []
    results = cursor.fetchall()
    for search in results:
        # Get sections for this search
        cursor.execute(
            """
            SELECT ss.order, ss.content, ss.title
            FROM search_section ss
            WHERE ss.search_fk = %s
            ORDER BY `order`
        """,
            (search["id"],),
        )

        sections = cursor.fetchall()

        # Skip if any section has no content
        if any(not section["content"] for section in sections):
            continue

        content = combine_search_gens_to_article(
            introduction=search["introduction"],
            sections=[
                {
                    "title": section["title"],
                    "content": section["content"],
                }
                for section in sections
            ],
        )

        if use_citations:
            cursor.execute(
                """
                SELECT sd.order, sd.url 
                FROM search_doc sd 
                WHERE sd.search_fk = %s
            """,
                (search["id"],),
            )

            docs = cursor.fetchall()
            seen_orders = set()

            for doc in docs:
                if doc["order"] in seen_orders:
                    continue
                content = content.replace(
                    f"[{doc['order']}]", f"[[{doc['order']}]]({doc['url']})"
                )
                seen_orders.add(doc["order"])

        # Clean up content
        content = clean_content(content)

        if len(content) < 500:
            print(f"Content too short for {search['identifier']}, skipping...")
            continue

        # Convert to HTML
        content = markdown.markdown(content)

        search_results.append(
            {
                "identifier": search["identifier"],
                "content": content,
                "one_liner": (
                    search["one_liner"]
                    if search["one_liner"] and len(search["one_liner"]) <= 100
                    else None
                ),
                "excerpt": (
                    search["excerpt"]
                    if search["excerpt"] and len(search["excerpt"]) <= 255
                    else None
                ),
            }
        )

    cursor.close()
    return search_results
