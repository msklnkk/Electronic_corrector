import sys

from alembic.config import CommandLine, Config

from corrector.application import database


class Settings:
    db = database.Settings()


def make_config():
    config = Config()
    config.set_main_option('script_location', Settings.db.ALEMBIC_SCRIPT_LOCATION)
    config.set_main_option('version_locations', Settings.db.ALEMBIC_VERSION_LOCATIONS)
    config.set_main_option('sqlalchemy.url', Settings.db.DATABASE_URL)
    config.set_main_option('file_template', Settings.db.ALEMBIC_MIGRATION_FILENAME_TEMPLATE)
    # config.set_main_option('timezone', 'UTC')

    return config


def run_cmd(*args):
    cli = CommandLine()
    cli.run_cmd(make_config(), cli.parser.parse_args(args))


if __name__ == '__main__':
    run_cmd(*sys.argv[1:])
