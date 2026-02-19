"""timezone aware datetime columns

Revision ID: 001
Revises: 
Create Date: 2026-02-10 15:23:20.123456

"""
from alembic import op
import sqlalchemy as sa
from datetime import timezone
from sqlalchemy.sql import func

# revision identifiers
revision = '001_timezone_aware_approach_time'
down_revision = 'af40b2e2c8ce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update the approach_time column to be timezone-aware
    # We need to cast the existing values to timestamptz
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN approach_time TYPE TIMESTAMP WITH TIME ZONE USING approach_time AT TIME ZONE 'UTC'")
    
    # Update the sentry_last_update column in threat_assessment_models to be timezone-aware
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN sentry_last_update TYPE TIMESTAMP WITH TIME ZONE USING sentry_last_update AT TIME ZONE 'UTC'")
    
    # Update the base table columns (created_at, updated_at) to be timezone-aware
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE asteroid_models ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE asteroid_models ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    # Revert the approach_time column to be timezone-naive
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN approach_time TYPE TIMESTAMP WITHOUT TIME ZONE USING approach_time AT TIME ZONE 'UTC'")
    
    # Revert the sentry_last_update column to be timezone-naive
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN sentry_last_update TYPE TIMESTAMP WITHOUT TIME ZONE USING sentry_last_update AT TIME ZONE 'UTC'")
    
    # Revert the base table columns to be timezone-naive
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE close_approach_models ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE asteroid_models ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE asteroid_models ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE threat_assessment_models ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")