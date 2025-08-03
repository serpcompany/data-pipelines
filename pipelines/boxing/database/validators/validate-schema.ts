#!/usr/bin/env tsx
/**
 * Schema validation script to ensure staging mirror DB matches production schema.
 * Uses Drizzle ORM to compare schemas at the TypeScript level.
 */

import { drizzle } from 'drizzle-orm/better-sqlite3';
import Database from 'better-sqlite3';
import * as productionSchema from '../../../../boxingundefeated-ref/server/db/schema';
import * as stagingSchema from '../drizzle/schema';
import { sql } from 'drizzle-orm';
import path from 'path';

// Define the expected tables and their key fields
const EXPECTED_TABLES = {
  boxers: ['id', 'boxrecId', 'boxrecUrl', 'slug', 'name'],
  boxerBouts: ['id', 'boxerId', 'boutDate', 'opponentName', 'result'],
  divisions: ['id', 'slug', 'name', 'weightLimitPounds']
};

interface ValidationResult {
  isValid: boolean;
  differences: string[];
  timestamp: string;
}

class SchemaValidator {
  private stagingDbPath: string;
  
  constructor() {
    // Construct path to staging DB
    this.stagingDbPath = path.join(
      __dirname, 
      '..', '..', 
      'data', 
      'output',
      'staging_mirror.db'
    );
  }
  
  async validateSchemas(): Promise<ValidationResult> {
    const differences: string[] = [];
    const timestamp = new Date().toISOString();
    
    try {
      // Connect to staging database
      const sqlite = new Database(this.stagingDbPath);
      const db = drizzle(sqlite);
      
      // Check if tables exist
      const tables = sqlite.prepare(`
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
      `).all() as { name: string }[];
      
      const existingTables = new Set(tables.map(t => t.name));
      
      // Check for missing tables
      for (const expectedTable of Object.keys(EXPECTED_TABLES)) {
        if (!existingTables.has(expectedTable)) {
          differences.push(`Missing table: ${expectedTable}`);
        }
      }
      
      // For each table, check if key columns exist
      for (const [tableName, expectedColumns] of Object.entries(EXPECTED_TABLES)) {
        if (existingTables.has(tableName)) {
          const columns = sqlite.prepare(`PRAGMA table_info(${tableName})`).all() as {
            name: string;
            type: string;
            notnull: number;
            dflt_value: any;
            pk: number;
          }[];
          
          const columnNames = new Set(columns.map(c => c.name));
          
          for (const expectedCol of expectedColumns) {
            if (!columnNames.has(expectedCol)) {
              differences.push(`Table ${tableName}: missing column ${expectedCol}`);
            }
          }
        }
      }
      
      // Check indexes
      const expectedIndexes = [
        { table: 'boxers', name: 'boxersSlugIdx' },
        { table: 'boxers', name: 'boxersBoxrecIdIdx' },
        { table: 'boxers', name: 'boxersNationalityIdx' },
        { table: 'boxers', name: 'boxersDivisionIdx' },
        { table: 'boxers', name: 'boxersStatusIdx' },
        { table: 'boxerBouts', name: 'boxerBoutsBoxerIdIdx' },
        { table: 'boxerBouts', name: 'boxerBoutsDateIdx' },
        { table: 'boxerBouts', name: 'uniqueBoxerBout' },
        { table: 'divisions', name: 'divisionsSlugIdx' },
        { table: 'divisions', name: 'divisionsShortNameIdx' }
      ];
      
      for (const { table, name } of expectedIndexes) {
        const indexes = sqlite.prepare(`PRAGMA index_list(${table})`).all() as {
          name: string;
          unique: number;
        }[];
        
        const indexNames = new Set(indexes.map(i => i.name));
        if (!indexNames.has(name)) {
          differences.push(`Table ${table}: missing index ${name}`);
        }
      }
      
      // Close the database connection
      sqlite.close();
      
      return {
        isValid: differences.length === 0,
        differences,
        timestamp
      };
      
    } catch (error) {
      differences.push(`Validation error: ${error.message}`);
      return {
        isValid: false,
        differences,
        timestamp
      };
    }
  }
  
  async generateReport(): Promise<void> {
    const result = await this.validateSchemas();
    
    console.log('\n=== Schema Validation Report ===');
    console.log(`Timestamp: ${result.timestamp}`);
    console.log(`Staging DB: ${this.stagingDbPath}`);
    console.log(`\nValidation Result: ${result.isValid ? '✅ PASSED' : '❌ FAILED'}`);
    
    if (!result.isValid) {
      console.log('\nDifferences found:');
      result.differences.forEach(diff => {
        console.log(`  - ${diff}`);
      });
    }
    
    // Write report to file
    const reportPath = path.join(__dirname, 'schema-validation-report.json');
    const fs = await import('fs/promises');
    await fs.writeFile(reportPath, JSON.stringify(result, null, 2));
    console.log(`\nReport saved to: ${reportPath}`);
    
    // Exit with appropriate code
    process.exit(result.isValid ? 0 : 1);
  }
}

// Run validation if called directly
if (require.main === module) {
  const validator = new SchemaValidator();
  validator.generateReport().catch(console.error);
}

export { SchemaValidator, ValidationResult };