#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import * as fs from 'fs/promises';
import * as path from 'path';
import { sql } from 'drizzle-orm';

// Load environment
dotenv.config({ path: '../.env' });

interface UploadStats {
  total: number;
  uploaded: number;
  updated: number;
  skipped: number;
  errors: number;
}

async function uploadHtmlFilesToStaging() {
  console.log('📤 Uploading HTML files to staging database...\n');

  const connectionString = `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DEFAULT_DB}`;
  
  const client = postgres(connectionString);
  const db = drizzle(client);

  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  const stats: UploadStats = {
    total: 0,
    uploaded: 0,
    updated: 0,
    skipped: 0,
    errors: 0
  };

  try {
    // Get all HTML files
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files.filter(f => 
      f.endsWith('.html') && 
      f.startsWith('en_box-pro') && 
      !f.includes('Login') &&
      !f.includes('login')
    );

    stats.total = htmlFiles.length;
    console.log(`📊 Found ${stats.total} HTML files to process\n`);

    // Process files in batches
    const batchSize = 100;
    for (let i = 0; i < htmlFiles.length; i += batchSize) {
      const batch = htmlFiles.slice(i, i + batchSize);
      console.log(`📦 Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(htmlFiles.length/batchSize)} (${batch.length} files)...`);

      await Promise.all(batch.map(async (filename) => {
        try {
          // Extract BoxRec ID from filename
          const match = filename.match(/box-pro_(\d+)\.html$/);
          if (!match) {
            stats.errors++;
            console.log(`⚠️  Skipping ${filename} - invalid format`);
            return;
          }

          const boxrecId = match[1];
          const htmlPath = path.join(htmlDir, filename);
          
          // Read HTML content
          const htmlContent = await fs.readFile(htmlPath, 'utf-8');
          
          // Skip login pages
          if (htmlContent.includes('Please login to continue') || 
              htmlContent.includes('Login to BoxRec') ||
              htmlContent.includes('<title>BoxRec: Login</title>')) {
            stats.skipped++;
            return;
          }

          // Extract basic info for the database
          const boxrecUrl = `https://boxrec.com/en/box-pro/${boxrecId}`;
          const titleMatch = htmlContent.match(/<title>BoxRec:\s*([^<]+)<\/title>/);
          const boxerName = titleMatch ? titleMatch[1].trim() : `Boxer ${boxrecId}`;
          const slug = boxerName.toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim();

          // Upsert - insert or update in one query
          await db.execute(sql`
            INSERT INTO "data-pipelines-staging"."boxers" (
              id,
              boxrec_id,
              boxrec_url,
              slug,
              full_name,
              html_file,
              created_at,
              updated_at
            ) VALUES (
              gen_random_uuid(),
              ${boxrecId},
              ${boxrecUrl},
              ${slug + '-' + boxrecId},
              ${boxerName},
              ${htmlContent},
              CURRENT_TIMESTAMP,
              CURRENT_TIMESTAMP
            )
            ON CONFLICT (boxrec_id) 
            DO UPDATE SET 
              html_file = EXCLUDED.html_file,
              boxrec_url = EXCLUDED.boxrec_url,
              full_name = EXCLUDED.full_name,
              slug = EXCLUDED.slug,
              updated_at = CURRENT_TIMESTAMP
          `);
          stats.uploaded++;

        } catch (error) {
          stats.errors++;
          console.error(`❌ Error processing ${filename}:`, error);
        }
      }));

      // Progress update
      const processed = Math.min((i + batchSize), htmlFiles.length);
      console.log(`   ✅ Processed ${processed}/${stats.total} files (${Math.round((processed/stats.total)*100)}%)`);
    }

    console.log('\n📈 Upload Summary:');
    console.log(`📊 Total files: ${stats.total}`);
    console.log(`✅ New uploads: ${stats.uploaded}`);
    console.log(`🔄 Updated: ${stats.updated}`);
    console.log(`⏭️  Skipped (login pages): ${stats.skipped}`);
    console.log(`❌ Errors: ${stats.errors}`);

    // Verify upload
    const totalCount = await db.execute(sql`
      SELECT COUNT(*) as count FROM "data-pipelines-staging"."boxers" 
      WHERE html_file IS NOT NULL
    `);

    console.log(`\n📊 Total HTML records in database: ${totalCount.rows?.[0]?.count || 0}`);

  } catch (error) {
    console.error('❌ Fatal error:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Run the upload
uploadHtmlFilesToStaging().catch(console.error);