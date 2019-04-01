#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pigpio
import time
import paho.mqtt.client
import click
import click_log
import logging

PIN_HORIZONTAL = 17
PIN_VERTICAL = 18

logging.basicConfig(format='%(asctime)s %(message)s')


class Servo():
    def __init__(self, pin, min_pulsewidth=500, max_pulsewidth=2500):
        self._pin = pin
        self._min_pulsewidth = min_pulsewidth
        self._max_pulsewidth = max_pulsewidth
        self._angle = None
        self._gpio = pigpio.pi()
        self.off()

    def __del__(self):
        self.off()
        time.sleep(0.02)
    
    def set_angle(self, angle):
        if angle > 180:
            angle = 180
        elif  angle < 0:
            angle = 0

        pulsewidth = ((self._max_pulsewidth - self._min_pulsewidth) * (angle / 180.0)) + self._min_pulsewidth

        self._gpio.set_servo_pulsewidth(self._pin, pulsewidth)

        self._angle = angle

    def get_angle(self):
        return self._angle
        
    def off(self):
        self._gpio.set_servo_pulsewidth(self._pin, 0)


def mqtt_on_connect(mqttc, userdata, flags, rc):
    logging.info('Connected to MQTT broker with code %s', rc)

    for topic in ('servo/vertical/angle/set', 
                  'servo/vertical/angle/get',
                  'servo/horizontal/angle/set',
                  'servo/horizontal/angle/get'):
        logging.debug('Subscribe: %s', topic)
        mqttc.subscribe(topic)


def mqtt_on_disconnect(mqttc, userdata, rc):
    logging.info('Disconnect from MQTT broker with code %s', rc)


def mqtt_on_message(mqttc, userdata, message):
    logging.debug('Message %s %s', message.topic, message.payload)

    servo = userdata.get(message.topic[6], None)

    if not servo:
        return

    if message.topic == 'servo/vertical/angle/set':
        servo.set_angle(int(message.payload))
        
    elif message.topic == 'servo/horizontal/angle/set':
        servo.set_angle(int(message.payload))

    mqttc.publish(message.topic[:-4], servo.get_angle())


@click.command()
@click.option('--host', type=click.STRING, default="127.0.0.1", help="MQTT host to connect to [default: 127.0.0.1].")
@click.option('--port', type=click.IntRange(0, 65535), default=1883, help="MQTT port to connect to [default: 1883].")
@click.option('--username', type=click.STRING, help="MQTT username.")
@click.option('--password', type=click.STRING, help="MQTT password.")
@click.option('--cafile', type=click.Path(exists=True), help="MQTT cafile.")
@click.option('--certfile', type=click.Path(exists=True), help="MQTT certfile.")
@click.option('--keyfile', type=click.Path(exists=True), help="MQTT keyfile.")
@click_log.simple_verbosity_option(default='INFO')
def run(host, port, username, password, cafile, certfile, keyfile):
    logging.info("Process started")

    horizontal = Servo(PIN_HORIZONTAL)
    vertical = Servo(PIN_VERTICAL)

    mqttc = paho.mqtt.client.Client(userdata={"h": horizontal, "v": vertical})
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