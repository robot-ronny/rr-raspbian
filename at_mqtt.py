#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import paho.mqtt.client
import click
import click_log
import logging
from at_serial import ATSerial

logging.basicConfig(format='%(asctime)s %(message)s')


def mqtt_on_connect(mqttc, userdata, flags, rc):
    logging.info('Connected to MQTT broker with code %s', rc)

    for topic in ('at/+', ):
        logging.debug('Subscribe: %s', topic)
        mqttc.subscribe(topic)


def mqtt_on_disconnect(mqttc, userdata, rc):
    logging.info('Disconnect from MQTT broker with code %s', rc)


def mqtt_on_message(mqttc, userdata, message):
    logging.debug('Message %s %s', message.topic, message.payload)

    cmd = message.topic.split('/')[1]

    cmd = '$' + cmd.upper() + '=' + message.payload.decode()

    logging.debug("at cmd %s", cmd)

    userdata['at'].command(cmd)



@click.command()
@click.option('--device', type=click.STRING, help="Device path.")
@click.option('--host', type=click.STRING, default="127.0.0.1", help="MQTT host to connect to [default: 127.0.0.1].")
@click.option('--port', type=click.IntRange(0, 65535), default=1883, help="MQTT port to connect to [default: 1883].")
@click.option('--username', type=click.STRING, help="MQTT username.")
@click.option('--password', type=click.STRING, help="MQTT password.")
@click.option('--cafile', type=click.Path(exists=True), help="MQTT cafile.")
@click.option('--certfile', type=click.Path(exists=True), help="MQTT certfile.")
@click.option('--keyfile', type=click.Path(exists=True), help="MQTT keyfile.")
@click_log.simple_verbosity_option(default='INFO')
def run(device, host, port, username, password, cafile, certfile, keyfile):
    logging.info("Process started")

    at = ATSerial(device)

    mqttc = paho.mqtt.client.Client(userdata={"at": at})
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    mqttc.on_disconnect = mqtt_on_disconnect

    if username:
        mqttc.username_pw_set(username, password)

    if cafile:
        mqttc.tls_set(cafile, certfile, keyfile)

    mqttc.connect(host, port, keepalive=10)
    mqttc.loop_forever()


if __name__ == "__main__":
    run()
