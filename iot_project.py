from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
import RPi.GPIO as GPIO
from picamera import PiCamera

# path where the captured image will be saved
filePath = "~/captured.jpg"
# Light bulb and push button pins
led_pin = 17
button_pin = 6

# MQTT configurations
host = "#<amazon aws url>"
port = 8883
rootCAPath="#<pem file> e.g.: ~/aws.pem"
privateKeyPath="#<private key> e.g.: ~/aws.pem.key"
certificatePath="#<certificate_file> e.g.: ~/aws.pem.crt"

# Current state
state = -1

def turn_led():
    global state
    if state == -1:
        print("Turning OFF the LED")
        GPIO.output(led_pin, GPIO.LOW)
    else:
        print("Turning ON the LED")
        GPIO.output(led_pin, GPIO.HIGH)

    capture()
    publish_image()

def on_push_down(channel):
    print("Button pushed")
    global state
    state = -state
    awsIoTClient.publishAsync("my_pi/button", "%s" % state, 1)
    turn_led()

# Callback when subscribing to a topic asynchornously
def on_subscribe(mid, data):
    print("** Subscription callback")

# Custom MQTT message callback
def on_message(message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    global state
    if message.payload == "1":
        state = 1
    else:
        state = -1
    turn_led()

# Capture picture
def capture():
    print("Capturing image...")
    camera.resolution = (300, 300)
    camera.start_preview()
    time.sleep(2)
    camera.capture(filePath)
    camera.stop_preview()
    print("Image captured!")

# Publish image
def publish_image():
    print("Publishing image...")
    imageFile = open(filePath, mode="rb")
    imageData = bytearray(imageFile.read())
    awsIoTClient.publishAsync("my_pi/camera", imageData, 1)
    print("Image published...")


camera = PiCamera()

# Initialize push button
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(led_pin, GPIO.OUT)

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(button_pin, GPIO.RISING)
GPIO.add_event_callback(button_pin, callback=on_push_down)

# Turn off the LED
GPIO.output(led_pin, GPIO.LOW)

# Initialize MQTT
awsIoTClient = AWSIoTMQTTClient("my_raspberry_pi_ID") #clientId can be anything
awsIoTClient.configureEndpoint(host, port)
awsIoTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
awsIoTClient.configureAutoReconnectBackoffTime(1, 32, 20)
awsIoTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
awsIoTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
awsIoTClient.configureConnectDisconnectTimeout(10)  # 10 sec
awsIoTClient.configureMQTTOperationTimeout(15)  # 5 sec
awsIoTClient.onMessage = on_message

#Connect and subscribe to AWS IoT
awsIoTClient.connect()
awsIoTClient.subscribeAsync("my_pi/led", 1, ackCallback=on_subscribe)
while True:
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        GPIO.cleanup()
        awsIoTClient.disconnect()
        exit(0)
