#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import { sql } from 'drizzle-orm';
import * as cheerio from 'cheerio';
import { v4 as uuidv4 } from 'uuid';

// Load environment
dotenv.config({ path: '../.env' });

interface BoxerRecord {
  wins: number;
  winsByKO: number;
  losses: number;
  lossesByKO: number;
  draws: number;
}

interface ParsedBoxer {
  id: string;
  boxrecId: string;
  boxrecUrl: string;
  slug: string;
  fullName: string;
  birthName?: string;
  nickname?: string;
  gender?: string;
  avatarImage?: string;
  residence?: string;
  birthPlace?: string;
  dateOfBirth?: string;
  nationality?: string;
  height?: string;
  reach?: string;
  weight?: string;
  stance?: string;
  bio?: string;
  proRecord?: BoxerRecord;
  proDivision?: string;
  proStatus?: string;
  proDebutDate?: string;
}

class BoxRecHTMLParser {
  private $: cheerio.CheerioAPI;

  constructor(html: string) {
    this.$ = cheerio.load(html);
  }

  parse(boxrecId: string, boxrecUrl: string): ParsedBoxer {
    const $ = this.$;
    
    // Extract name
    const fullName = $('h1').first().text().trim() || 'Unknown';
    
    // Generate slug if not provided
    const slug = fullName.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');

    // Extract image
    const avatarImage = $('.profilePhoto img').attr('src') || 
                       $('img[alt*="' + fullName + '"]').first().attr('src');

    // Extract basic info from table rows
    const infoRows = $('.rowTable');
    const info: Record<string, string> = {};
    
    infoRows.each((_, row) => {
      const label = $(row).find('.rowLabel').text().trim().toLowerCase();
      const value = $(row).find('.rowData').text().trim();
      if (label && value) {
        info[label] = value;
      }
    });

    // Extract record (wins-losses-draws)
    const recordText = $('.profileWLD').text() || '';
    const proRecord = this.parseRecord(recordText);

    // Extract bio
    const bio = $('.profileBio').text().trim() || undefined;

    return {
      id: uuidv4(),
      boxrecId,
      boxrecUrl,
      slug,
      fullName,
      birthName: info['birth name'] || undefined,
      nickname: info['alias'] || info['nickname'] || undefined,
      gender: info['sex'] || this.inferGender(fullName),
      avatarImage: avatarImage || undefined,
      residence: info['residence'] || undefined,
      birthPlace: info['birth place'] || info['birthplace'] || undefined,
      dateOfBirth: info['born'] || info['date of birth'] || undefined,
      nationality: info['nationality'] || undefined,
      height: info['height'] || undefined,
      reach: info['reach'] || undefined,
      weight: info['weight'] || undefined,
      stance: info['stance']?.toLowerCase() || undefined,
      bio,
      proRecord,
      proDivision: info['division'] || undefined,
      proStatus: info['status']?.toLowerCase() || undefined,
      proDebutDate: info['debut'] || undefined,
    };
  }

  private parseRecord(recordText: string): BoxerRecord {
    // Parse format like "50-0-0 (44 KOs)"
    const match = recordText.match(/(\d+)-(\d+)-(\d+)(?:\s*\((\d+)\s*KOs?\))?/);
    
    if (match) {
      return {
        wins: parseInt(match[1]) || 0,
        losses: parseInt(match[2]) || 0,
        draws: parseInt(match[3]) || 0,
        winsByKO: parseInt(match[4]) || 0,
        lossesByKO: 0, // This usually needs to be parsed from bout history
      };
    }
    
    return {
      wins: 0,
      winsByKO: 0,
      losses: 0,
      lossesByKO: 0,
      draws: 0,
    };
  }

  private inferGender(name: string): string {
    // Simple inference - would need improvement for production
    // Check for common female boxing indicators
    const femaleIndicators = ['amanda', 'katie', 'claressa', 'laila'];
    const nameLower = name.toLowerCase();
    
    if (femaleIndicators.some(indicator => nameLower.includes(indicator))) {
      return 'female';
    }
    
    return 'male'; // Default assumption
  }
}

async function parseHtmlToDbFields() {
  console.log('🔄 Parsing HTML files to database fields...\n');

  const connectionString = `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DEFAULT_DB}`;
  
  const client = postgres(connectionString);
  const db = drizzle(client);

  try {
    // Get unparsed HTML files
    const unparsedRecords = await db.execute(sql`
      SELECT 
        id,
        boxrec_id,
        boxrec_url,
        html_file
      FROM "data-pipelines-staging"."boxers"
      WHERE html_file IS NOT NULL 
      AND html_parsed_at IS NULL
      LIMIT 10
    `);

    console.log(`📊 Found ${unparsedRecords.rows.length} HTML files to parse\n`);

    let successCount = 0;
    let errorCount = 0;

    for (const record of unparsedRecords.rows) {
      try {
        console.log(`Parsing boxer: ${record.boxrec_id}...`);
        
        const parser = new BoxRecHTMLParser(record.html_file as string);
        const parsed = parser.parse(
          record.boxrec_id as string,
          record.boxrec_url as string
        );

        // Update the record with parsed data
        await db.execute(sql`
          UPDATE "data-pipelines-staging"."boxers"
          SET 
            full_name = ${parsed.fullName},
            birth_name = ${parsed.birthName},
            nickname = ${parsed.nickname},
            gender = ${parsed.gender},
            avatar_image = ${parsed.avatarImage},
            residence = ${parsed.residence},
            birth_place = ${parsed.birthPlace},
            date_of_birth = ${parsed.dateOfBirth},
            nationality = ${parsed.nationality},
            height = ${parsed.height},
            reach = ${parsed.reach},
            weight = ${parsed.weight},
            stance = ${parsed.stance},
            bio = ${parsed.bio},
            pro_wins = ${parsed.proRecord?.wins || 0},
            pro_wins_by_knockout = ${parsed.proRecord?.winsByKO || 0},
            pro_losses = ${parsed.proRecord?.losses || 0},
            pro_losses_by_knockout = ${parsed.proRecord?.lossesByKO || 0},
            pro_draws = ${parsed.proRecord?.draws || 0},
            pro_division = ${parsed.proDivision},
            pro_status = ${parsed.proStatus},
            pro_debut_date = ${parsed.proDebutDate},
            pro_total_bouts = ${(parsed.proRecord?.wins || 0) + (parsed.proRecord?.losses || 0) + (parsed.proRecord?.draws || 0)},
            html_parsed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
          WHERE id = ${record.id}
        `);

        console.log(`✅ Parsed: ${parsed.fullName} (${parsed.proRecord?.wins}-${parsed.proRecord?.losses}-${parsed.proRecord?.draws})`);
        successCount++;

      } catch (error) {
        console.error(`❌ Error parsing ${record.boxrec_id}:`, error);
        
        // Log parse error
        await db.execute(sql`
          UPDATE "data-pipelines-staging"."boxers"
          SET 
            parse_errors = ${String(error)},
            updated_at = CURRENT_TIMESTAMP
          WHERE id = ${record.id}
        `);
        
        errorCount++;
      }
    }

    console.log(`\n📈 Parsing complete:`);
    console.log(`✅ Success: ${successCount}`);
    console.log(`❌ Errors: ${errorCount}`);

    // Show sample of parsed data
    const sample = await db.execute(sql`
      SELECT 
        full_name,
        pro_wins,
        pro_losses,
        pro_draws,
        nationality,
        pro_division
      FROM "data-pipelines-staging"."boxers"
      WHERE html_parsed_at IS NOT NULL
      LIMIT 5
    `);

    console.log('\n📋 Sample parsed boxers:');
    sample.rows.forEach(boxer => {
      console.log(`- ${boxer.full_name}: ${boxer.pro_wins}-${boxer.pro_losses}-${boxer.pro_draws}, ${boxer.nationality}, ${boxer.pro_division}`);
    });

  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Run the parser
parseHtmlToDbFields().catch(console.error);