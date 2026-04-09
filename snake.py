import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

# distance sensor
TRIG = 26
ECHO = 21

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# motor pins (fix later)
motors = [
    (5, 6, 12),
    (13, 19, 18),
    (16, 20, 25),
    (22, 23, 24),
    (8, 7, 3),
    (9, 10, 11)
]

pwm_list = []

# setup motors
# IN1 = HIGH, IN2 = LOW → forward
# IN1 = LOW, IN2 = HIGH → backward
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
    time.sleep(0.002)

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

# slither (idk if this would work LMFAO)
def slither_forward(base_speed=0.6, cycles=3, delay=0.08):
    for _ in range(cycles):
        for i in range(6):
            offset = 0.15 * (i % 2)  # Slight lateral bias per motor
            set_motor(i, base_speed + offset if i % 2 == 0 else base_speed - offset)
            time.sleep(delay)

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

    while True:
        dist = get_distance()
        print("Distance:", dist, "cm")

        # Detection threshold
        if dist < 50:
            print("Target detected!")

            # Calculate velocity
            velocity, prev_dist, prev_time = get_velocity(prev_dist, prev_time)
            print("Velocity:", velocity)

            # Convert velocity to motor speed
            speed = min(max(0.3, abs(velocity) + 0.2), 1.0)

            print("Chasing at speed:", speed)

            # Chase
            slither_forward(speed)
            time.sleep(2)

            # Return
            print("Returning...")
            move_backward(speed)
            time.sleep(2)

            stop_all()

        else:
            stop_all()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Stopping...")
    stop_all()
    GPIO.cleanup()