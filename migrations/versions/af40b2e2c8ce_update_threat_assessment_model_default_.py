"""Update threat assessment model default values

Revision ID: af40b2e2c8ce
Revises: 3715b771480f
Create Date: 2026-02-08 19:08:29.176825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af40b2e2c8ce'
down_revision: Union[str, None] = '3715b771480f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update default values for threat_assessment_models table
    op.alter_column('threat_assessment_models', 'designation',
                   server_default='')
    op.alter_column('threat_assessment_models', 'fullname',
                   server_default='')
    op.alter_column('threat_assessment_models', 'ip',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'ts_max',
                   server_default='0')
    op.alter_column('threat_assessment_models', 'ps_max',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'diameter',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'v_inf',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'h',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'n_imp',
                   server_default='0')
    op.alter_column('threat_assessment_models', 'last_obs',
                   server_default='')
    op.alter_column('threat_assessment_models', 'threat_level_ru',
                   server_default='')
    op.alter_column('threat_assessment_models', 'torino_scale_ru',
                   server_default='')
    op.alter_column('threat_assessment_models', 'impact_probability_text_ru',
                   server_default='')
    op.alter_column('threat_assessment_models', 'energy_megatons',
                   server_default='0.0')
    op.alter_column('threat_assessment_models', 'impact_category',
                   server_default='локальный')


def downgrade() -> None:
    # Revert default values for threat_assessment_models table
    op.alter_column('threat_assessment_models', 'designation',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'fullname',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'ip',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'ts_max',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'ps_max',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'diameter',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'v_inf',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'h',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'n_imp',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'last_obs',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'threat_level_ru',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'torino_scale_ru',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'impact_probability_text_ru',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'energy_megatons',
                   server_default=None)
    op.alter_column('threat_assessment_models', 'impact_category',
                   server_default=None)
