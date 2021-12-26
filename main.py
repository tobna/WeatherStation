import Adafruit_DHT
import argparse


def main(temp_data_pin):
    dht22 = Adafruit_DHT.DHT22
    hum, temp = Adafruit_DHT.read_retry(dht22, temp_data_pin)
    print(f"read temp={temp}°C\thum={hum}%")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-pt', '--pin_temp', type=int, default=2, nargs='?',
                        help="GPIO pin number for data of DHT22 sensor")
    args = parser.parse_args()
    temp_data_pin = args.pin_temp

    main(temp_data_pin)
