import RPi.GPIO as GPIO
import argparse
import time
import logging
import sqlite3
import uuid

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize SQLite3 database
conn = sqlite3.connect('audit_log.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (timestamp TEXT, log_message TEXT, execution_id TEXT)''')
conn.commit()

# Generate a unique execution_id for this run
execution_id = str(uuid.uuid4())


class SQLiteHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        cursor.execute("INSERT INTO logs (timestamp, log_message, execution_id) VALUES (?, ?, ?)",
                       (time.strftime("%Y-%m-%d %H:%M:%S"), msg, execution_id))
        conn.commit()


# Mend SQLiteHandler to the Logging Function.
logger = logging.getLogger()
logger.addHandler(SQLiteHandler())


def initialize_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(drain_pin, GPIO.OUT)
    GPIO.output(drain_pin, GPIO.HIGH)
    for flood_pin in flood_pins:
        GPIO.setup(flood_pin, GPIO.OUT)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--drain', action='store_true', help='Drain Flood Table Top', required=False,
                        default=False)
    parser.add_argument('-f', '--flood', action='store_true', help='Flood Only', required=False, default=False)
    parser.add_argument('-n', '--seconds_to_drain', help='How many seconds to drain, if draining.', type=int,
                        default=60, required=False)
    return parser.parse_args()


def perform_watering():
    for flood_pin in flood_pins:
        GPIO.output(flood_pin, True)
    logging.info(f'Flooding has begun and is scheduled to flood for {round(flood_time / 60, 2)} minutes.')
    time.sleep(flood_time)
    for flood_pin in flood_pins:
        GPIO.output(flood_pin, False)
    logging.info(f'Flooding complete and will now hold for {round(hold_time / 60, 2)} minutes.')
    time.sleep(hold_time)
    logging.info('Hold Time Complete.')


def perform_draining(seconds_int):
    GPIO.output(drain_pin, GPIO.LOW)
    logging.info('Solenoid Opened')
    time.sleep(seconds_int)
    GPIO.output(drain_pin, GPIO.HIGH)
    logging.info('Solenoid Closed')


def main(_args, _default_drain_time):
    try:
        if _args.drain and _args.flood:
            logging.error("Both drain and flood flags cannot be set simultaneously.")
            return

        if _args.drain:
            logging.info(f'Drain Only Directive Received. Drain procedure will run for '
                         f'{round(_args.seconds_to_drain / 60, 2)} minutes.')
            perform_draining(_args.seconds_to_drain)
        elif _args.flood:
            logging.info(f'Flood Only Directive Received. Flood procedure will run for '
                         f'{round(flood_time / 60, 2)} minutes.')
            perform_watering()
            logging.info('Flooding now complete.')
        else:
            perform_watering()
            logging.info(f'Flooding and Holding periods complete. Now draining will occur for '
                         f'{round(_default_drain_time / 60, 2)} minutes.')
            perform_draining(_default_drain_time)
    except RuntimeError as e:
        logging.error(f"GPIO Runtime Error in main function: {e}")
    except Exception as e:
        logging.error(f'General Exception in main function: {e}')
    finally:
        GPIO.cleanup()
        conn.close()


if __name__ == "__main__":
    flood_pins = (17, 23)
    drain_pin = 18
    flood_time = 255
    hold_time = 600
    default_drain_time = 1200

    args = parse_args()
    initialize_gpio()
    main(args, default_drain_time)
