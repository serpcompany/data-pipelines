## mysql> DESCRIBE boxing_boxers;
+---------------------------------------------+-----------------+------+-----+---------+----------------+
| Field                                       | Type            | Null | Key | Default | Extra          |
+---------------------------------------------+-----------------+------+-----+---------+----------------+
| id                                          | int unsigned    | NO   | PRI | NULL    | auto_increment |
| created_at                                  | timestamp       | YES  |     | NULL    |                |
| boxer_name                                  | varchar(255)    | YES  |     | NULL    |                |
| boxer_name_sanitized                        | varchar(255)    | YES  |     | NULL    |                |
| boxer_nicknames                             | json            | YES  |     | NULL    |                |
| boxer_birthdate                             | date            | YES  |     | NULL    |                |
| boxer_deathdate                             | date            | YES  |     | NULL    |                |
| boxer_nationality                           | json            | YES  |     | NULL    |                |
| boxer_stance                                | varchar(255)    | YES  |     | NULL    |                |
| boxer_num_wins                              | int             | YES  |     | NULL    |                |
| boxer_num_losses                            | int             | YES  |     | NULL    |                |
| boxer_draws                                 | int             | YES  |     | NULL    |                |
| boxer_ko                                    | int             | YES  |     | NULL    |                |
| boxer_no_contest                            | int             | YES  |     | NULL    |                |
| boxer_image_url                             | varchar(1000)   | YES  |     | NULL    |                |
| boxer_bio                                   | mediumtext      | YES  |     | NULL    |                |
| boxer_people_table_fk                       | bigint unsigned | YES  | UNI | NULL    |                |
| boxer_weight_class                          | json            | YES  |     | NULL    |                |
| cloudflare_boxer_image_url                  | varchar(1000)   | YES  |     | NULL    |                |
| boxer_slug                                  | varchar(255)    | YES  | UNI | NULL    |                |
| boxer_description                           | mediumtext      | YES  |     | NULL    |                |
| boxer_article                               | mediumtext      | YES  |     | NULL    |                |
| boxer_title_wins                            | int             | YES  |     | NULL    |                |
| boxer_title_defenses                        | int             | YES  |     | NULL    |                |
| boxer_title_kos                             | int             | YES  |     | NULL    |                |
| boxer_losses_ko                             | int             | YES  |     | NULL    |                |
| boxer_birthplace                            | varchar(255)    | YES  |     | NULL    |                |
| boxer_debut                                 | date            | YES  |     | NULL    |                |
| boxer_ape_index                             | varchar(255)    | YES  |     | NULL    |                |
| division                                    | varchar(255)    | YES  |     | NULL    |                |
| rating                                      | int             | YES  |     | NULL    |                |
| birth_name                                  | varchar(255)    | YES  |     | NULL    |                |
| sex                                         | varchar(255)    | YES  |     | NULL    |                |
| alias                                       | varchar(255)    | YES  |     | NULL    |                |
| age                                         | int             | YES  |     | NULL    |                |
| residence                                   | varchar(255)    | YES  |     | NULL    |                |
| manager_agent                               | varchar(255)    | YES  |     | NULL    |                |
| promoter                                    | varchar(255)    | YES  |     | NULL    |                |
| status                                      | varchar(255)    | YES  |     | NULL    |                |
| profile_picture_url                         | varchar(1000)   | YES  |     | NULL    |                |
| height_imperial                             | varchar(32)     | YES  |     | NULL    |                |
| height_metric                               | varchar(32)     | YES  |     | NULL    |                |
| weight_imperial                             | varchar(32)     | YES  |     | NULL    |                |
| weight_metric                               | varchar(32)     | YES  |     | NULL    |                |
| bouts                                       | int             | YES  |     | NULL    |                |
| rounds                                      | int             | YES  |     | NULL    |                |
| career                                      | varchar(32)     | YES  |     | NULL    |                |
| debut                                       | varchar(32)     | YES  |     | NULL    |                |
| reach_imperial                              | varchar(32)     | YES  |     | NULL    |                |
| reach_metric                                | varchar(32)     | YES  |     | NULL    |                |
| ko_percent                                  | varchar(32)     | YES  |     | NULL    |                |
| boxrec_url                                  | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_name                       | varchar(255)    | YES  |     | NULL    |                |
| martialbot_total_fights                     | int             | YES  |     | NULL    |                |
| martialbot_wins                             | int             | YES  |     | NULL    |                |
| martialbot_losses                           | int             | YES  |     | NULL    |                |
| martialbot_draws                            | int             | YES  |     | NULL    |                |
| martialbot_no_contests                      | int             | YES  |     | NULL    |                |
| martialbot_ko_wins                          | int             | YES  |     | NULL    |                |
| martialbot_total_title_wins                 | int             | YES  |     | NULL    |                |
| martialbot_title_defenses                   | int             | YES  |     | NULL    |                |
| martialbot_title_fight_ko_wins              | int             | YES  |     | NULL    |                |
| martialbot_losses_via_ko                    | int             | YES  |     | NULL    |                |
| martialbot_boxer_nationality                | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_birthplace                 | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_nickname                   | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_date_of_birth              | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_debut                      | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_height                     | varchar(20)     | YES  |     | NULL    |                |
| martialbot_boxer_weight                     | varchar(20)     | YES  |     | NULL    |                |
| martialbot_boxer_reach                      | varchar(20)     | YES  |     | NULL    |                |
| martialbot_boxer_ape_index                  | varchar(20)     | YES  |     | NULL    |                |
| martialbot_boxer_stance                     | varchar(50)     | YES  |     | NULL    |                |
| boxer_professional_career_wikipedia_content | mediumtext      | YES  |     | NULL    |                |
| boxer_amateur_career_wikipedia_content      | mediumtext      | YES  |     | NULL    |                |
| boxer_personal_life_wikipedia_content       | mediumtext      | YES  |     | NULL    |                |
| boxer_wikidata_url                          | varchar(255)    | YES  |     | NULL    |                |
| boxer_wikidata_QID                          | varchar(255)    | YES  |     | NULL    |                |
| boxer_wikipedia_url                         | varchar(255)    | YES  |     | NULL    |                |
| boxer_boxrec_id                             | int             | YES  | UNI | NULL    |                |
| boxer_boxrec_url                            | varchar(255)    | YES  |     | NULL    |                |
| martialbot_url                              | varchar(255)    | YES  |     | NULL    |                |
| martialbot_career_summary                   | mediumtext      | YES  |     | NULL    |                |
| martialbot_career_highlights                | mediumtext      | YES  |     | NULL    |                |
| boxrec_image_url                            | varchar(255)    | YES  |     | NULL    |                |
| faq                                         | json            | YES  |     | NULL    |                |
| division_fk                                 | int unsigned    | YES  | MUL | NULL    |                |
| martialbot_excerpt                          | varchar(255)    | YES  |     | NULL    |                |
| martialbot_bio                              | mediumtext      | YES  |     | NULL    |                |
| martialbot_title_fights                     | int             | YES  |     | NULL    |                |
| martialbot_boxer_instagram                  | varchar(255)    | YES  |     | NULL    |                |
| martialbot_boxer_twitter                    | varchar(255)    | YES  |     | NULL    |                |
| martialbot_birthdate                        | date            | YES  |     | NULL    |                |
| martialbot_age                              | int             | YES  |     | NULL    |                |
| martialbot_debut                            | date            | YES  |     | NULL    |                |
| ghost_html                                  | mediumtext      | YES  |     | NULL    |                |
| google_search_chatgpt_boxer_image_url       | varchar(1000)   | YES  |     | NULL    |                |
| va_sourced_boxer_image_url                  | varchar(1000)   | YES  |     | NULL    |                |
+---------------------------------------------+-----------------+------+-----+---------+----------------+
98 rows in set (0.04 sec)


## mysql> DESCRIBE boxing_fights;
+--------------------+--------------+------+-----+-------------------+-------------------+
| Field              | Type         | Null | Key | Default           | Extra             |
+--------------------+--------------+------+-----+-------------------+-------------------+
| id                 | int unsigned | NO   | PRI | NULL              | auto_increment    |
| created_at         | timestamp    | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| fight_name         | varchar(255) | YES  |     | NULL              |                   |
| fight_nickname     | varchar(255) | YES  |     | NULL              |                   |
| boxer_a_side_id_fk | int unsigned | YES  | MUL | NULL              |                   |
| boxer_b_side_id_fk | int unsigned | YES  | MUL | NULL              |                   |
| venue              | varchar(255) | YES  |     | NULL              |                   |
| rounds             | varchar(10)  | YES  |     | NULL              |                   |
| time               | varchar(20)  | YES  |     | NULL              |                   |
| notes              | varchar(512) | YES  |     | NULL              |                   |
| date               | varchar(255) | YES  |     | NULL              |                   |
| type               | varchar(10)  | YES  |     | NULL              |                   |
| result             | varchar(55)  | YES  |     | NULL              |                   |
| slug               | varchar(255) | YES  |     | NULL              |                   |
| excerpt            | varchar(255) | YES  |     | NULL              |                   |
| content            | mediumtext   | YES  |     | NULL              |                   |
| boxrec_id          | int          | YES  | UNI | NULL              |                   |
+--------------------+--------------+------+-----+-------------------+-------------------+
17 rows in set (0.03 sec)

## mysql> DESCRIBE boxing_titles;
+-------+--------------+------+-----+---------+----------------+
| Field | Type         | Null | Key | Default | Extra          |
+-------+--------------+------+-----+---------+----------------+
| id    | int unsigned | NO   | PRI | NULL    | auto_increment |
| title | varchar(255) | NO   | UNI | NULL    |                |
+-------+--------------+------+-----+---------+----------------+
2 rows in set (0.04 sec)

## mysql> DESCRIBE boxing_weight_classes;
+--------------------+--------------+------+-----+-------------------+-------------------+
| Field              | Type         | Null | Key | Default           | Extra             |
+--------------------+--------------+------+-----+-------------------+-------------------+
| id                 | int unsigned | NO   | PRI | NULL              | auto_increment    |
| created_at         | timestamp    | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
| weight_class       | varchar(255) | NO   |     | NULL              |                   |
| weight_class_slug  | varchar(255) | NO   |     | NULL              |                   |
| professional       | tinyint(1)   | NO   |     | NULL              |                   |
| weight_limit_lbs   | int          | YES  | UNI | NULL              |                   |
| weight_limit_kg    | float        | YES  |     | NULL              |                   |
| weight_class_image | varchar(255) | YES  |     | NULL              |                   |
+--------------------+--------------+------+-----+-------------------+-------------------+
8 rows in set (0.04 sec)