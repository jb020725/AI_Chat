-- Add missing columns to leads table
-- This will store study levels, programs, and other missing information

-- Add study_level column
ALTER TABLE leads ADD COLUMN IF NOT EXISTS study_level VARCHAR(100);

-- Add program column  
ALTER TABLE leads ADD COLUMN IF NOT EXISTS program VARCHAR(255);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_study_level ON leads(study_level);
CREATE INDEX IF NOT EXISTS idx_leads_program ON leads(program);

-- Update existing leads to have empty values for new columns
UPDATE leads SET study_level = '' WHERE study_level IS NULL;
UPDATE leads SET program = '' WHERE program IS NULL;

-- Add comments to document the columns
COMMENT ON COLUMN leads.study_level IS 'Study level (e.g., Bachelor, Master, PhD, Diploma)';
COMMENT ON COLUMN leads.program IS 'Study field/program (e.g., Computer Science, Engineering, Business)';
