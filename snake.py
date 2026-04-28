import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# distance sensor
TRIG = 3
ECHO = 2 

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# motor pins IN, IN, EN
motors = [
    (24, 23, 18), # motor 1
    (25, 8, 7), # motor 2
    (16, 20, 12), # motor 3
    (21, 26, 19), # motor 4
    (6, 5, 13), # motor 5
    (9, 10, 11) # motor 6
]

pwm_list = []

# setup motors
# IN1 = HIGH, IN2 = LOW = forward
# IN1 = LOW, IN2 = HIGH = backward
for IN1, IN2, EN in motors:
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(EN, GPIO.OUT)

    pwm = GPIO.PWM(EN, 1000)
    pwm.start(0)
    pwm_list.append(pwm)

# distance measurement
def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start = time.time()
    end = time.time()

    while GPIO.input(ECHO) == 0:
        start = time.time()

    while GPIO.input(ECHO) == 1:
        end = time.time()

    duration = end - start
    distance = duration * 17150  # cm

    return round(distance, 2)

# motor control
def set_motor(i, speed):
    IN1, IN2, EN = motors[i]
    pwm = pwm_list[i]

    if speed > 0:
        GPIO.output(IN1, 1)
        GPIO.output(IN2, 0)
    elif speed < 0:
        GPIO.output(IN1, 0)
        GPIO.output(IN2, 1)
    else:
        GPIO.output(IN1, 0)
        GPIO.output(IN2, 0)

    pwm.ChangeDutyCycle(min(abs(speed) * 100, 100))

def stop_all():
    for i in range(6):
        set_motor(i, 0)

def move_forward(speed=0.6):
    for i in range(6):
        set_motor(i, speed)

def move_backward(speed=0.6):
    for i in range(6):
        set_motor(i, -speed)

# velocity calculation
def get_velocity(prev_dist, prev_time):
    curr_dist = get_distance()
    curr_time = time.time()

    velocity = (prev_dist - curr_dist) / (curr_time - prev_time)

    return velocity, curr_dist, curr_time


# main
try:
    prev_dist = get_distance()
    prev_time = time.time()
    print("Sensing...")

    while True:
        # Calculate velocity
        velocity, prev_dist, prev_time = get_velocity(prev_dist, prev_time)

        #Something was detected, chasing
        print("Velocity:", velocity, " cm/s")
        if velocity >= 5 or velocity <= -5:
            # Convert velocity to motor speed
            speed = min(max(( 0.01 * abs(velocity)), 0.2), 0.6)

            print("Chasing at speed: ", speed, " cm/s")

            # Chase
            move_forward(speed)
            time.sleep(5)
            stop_all()
            time.sleep(1)

            # Return
            print("Returning...")
            move_backward(speed)
            time.sleep(5)

            stop_all()
            time.sleep(1)

        else:
            stop_all()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Stopping...")
    stop_all()
    GPIO.cleanup()
    exit()
