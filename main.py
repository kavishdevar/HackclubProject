import RPi.GPIO as GPIO
from time import time, sleep
import random

GPIO.setmode(GPIO.BOARD)
RED = [40, 26, 37, 15]
YELLOW = [38, 8, 35, 13]
GREEN = [36, 10, 33, 11]
BUTTON = [32, 18, 31, 7]
BUZZER = 29

GPIO.setup(BUZZER, GPIO.OUT)
buzzer_pwm = GPIO.PWM(BUZZER, 440)
buzzer_pwm.start(0)

for i in range(4):
    GPIO.setup(RED[i], GPIO.OUT)
    GPIO.output(RED[i], GPIO.LOW)
    GPIO.setup(YELLOW[i], GPIO.OUT)
    GPIO.output(YELLOW[i], GPIO.LOW)
    GPIO.setup(GREEN[i], GPIO.OUT)
    GPIO.output(GREEN[i], GPIO.LOW)
    GPIO.setup(BUTTON[i], GPIO.IN,pull_up_down = GPIO.PUD_UP)

def generate_target_number():
    """Generate a random 4-digit number"""
    return [random.randint(1, 8) for _ in range(4)]

def display_all_leds(duration=0.5):
    """Flash all LEDs to signal game events"""
    for i in range(4):
        GPIO.output(RED[i], GPIO.HIGH)
        GPIO.output(YELLOW[i], GPIO.HIGH)
        GPIO.output(GREEN[i], GPIO.HIGH)
    sleep(duration)
    for i in range(4):
        GPIO.output(RED[i], GPIO.LOW)
        GPIO.output(YELLOW[i], GPIO.LOW)
        GPIO.output(GREEN[i], GPIO.LOW)

def provide_feedback(guess, target):
    """Provide Wordle-like feedback using LEDs"""
    for i in range(4):
        if guess[i] == target[i]:
            GPIO.output(GREEN[i], GPIO.HIGH)
        elif guess[i] in target:
            GPIO.output(YELLOW[i], GPIO.HIGH)
        else:
            GPIO.output(RED[i], GPIO.HIGH)
    
    if guess == target:
        sleep(1)
        for _ in range(3):
            for i in range(4):
                GPIO.output(GREEN[i], GPIO.LOW)
            sleep(0.3)
            for i in range(4):
                GPIO.output(GREEN[i], GPIO.HIGH)
            sleep(0.3)
        return True
    return False

def control_buzzer(intensity=0):
    """Control the buzzer with the given intensity (0-100)"""
    if intensity <= 0:
        buzzer_pwm.ChangeDutyCycle(0)
    else:
        capped_intensity = max(5, min(intensity, 100))
        buzzer_pwm.ChangeDutyCycle(capped_intensity)

def main():
    target_number = generate_target_number()
    print(f"Target number: {target_number}")
    
    display_all_leds(1.0)
    
    current_digits = [0, 0, 0, 0]
    confirmed_digits = [False, False, False, False]
    
    last = [0, 0, 0, 0]
    pressed = [False, False, False, False]
    
    challenge_interval = 30 * 60
    last_challenge_time = time()
    buzzer_active = False
    wrong_attempts = 0
    first_start = True
    while True:
        current_time = time()
        if (not buzzer_active and (current_time - last_challenge_time >= challenge_interval)) or (first_start):
            first_start = False
            print("BUZZER CHALLENGE ACTIVATED!")
            buzzer_active = True
            wrong_attempts = 0
            
            target_number = generate_target_number()
            print(f"New challenge target: {target_number}")
            
            current_digits = [0, 0, 0, 0]
            confirmed_digits = [False, False, False, False]
            display_all_leds(1.0)
        
        for i in range(4):
            if GPIO.input(BUTTON[i]) == GPIO.LOW:
                if not pressed[i]:
                    last[i] = current_time
                    pressed[i] = True
            else:
                if pressed[i]:
                    if current_time - last[i] > 0.75:
                        print(f"Position {i} confirmed as {current_digits[i]}")
                        confirmed_digits[i] = True
                        
                        GPIO.output(GREEN[i], GPIO.HIGH)
                        sleep(0.2)
                        GPIO.output(GREEN[i], GPIO.LOW)
                        
                        if all(confirmed_digits):
                            print(f"Guess: {current_digits}")
                            if provide_feedback(current_digits, target_number):
                                if buzzer_active:
                                    print("BUZZER CHALLENGE COMPLETED!")
                                    buzzer_active = False
                                    control_buzzer(0)
                                    last_challenge_time = current_time
                                
                                sleep(2)
                                for j in range(4):
                                    GPIO.output(RED[j], GPIO.LOW)
                                    GPIO.output(YELLOW[j], GPIO.LOW)
                                    GPIO.output(GREEN[j], GPIO.LOW)
                                
                                target_number = generate_target_number()
                                print(f"New target: {target_number}")
                                current_digits = [0, 0, 0, 0]
                                confirmed_digits = [False, False, False, False]
                                display_all_leds(1.0)
                            else:
                                if buzzer_active:
                                    wrong_attempts += 1
                                    new_intensity = min(10 + (wrong_attempts * 15), 95)
                                    print(f"Wrong attempt #{wrong_attempts}! Increasing buzzer intensity to {new_intensity}%")
                                    control_buzzer(new_intensity)
                                
                                sleep(3)
                                for j in range(4):
                                    GPIO.output(RED[j], GPIO.LOW)
                                    GPIO.output(YELLOW[j], GPIO.LOW)
                                    GPIO.output(GREEN[j], GPIO.LOW)
                                confirmed_digits = [False, False, False, False]
                    
                    elif current_time - last[i] > 0.05:
                        if not confirmed_digits[i]:
                            current_digits[i] = (current_digits[i] + 1) % 10
                            print(f"Position {i} digit: {current_digits[i]}")
                            
                            GPIO.output(YELLOW[i], GPIO.HIGH)
                            sleep(0.1)
                            GPIO.output(YELLOW[i], GPIO.LOW)
                    
                    last[i] = 0
                    pressed[i] = False
        
        sleep(0.01)

try:
    GPIO.output(RED[0], 1)
    sleep(1)
    GPIO.output(RED[0], 0)
    print("WORDLE NUMBER GAME STARTED - WITH BUZZER CHALLENGE!")
    main()
except Exception as e:
    print(f"Error: {e}")
    buzzer_pwm.stop()
    GPIO.cleanup()
finally:
    buzzer_pwm.stop()
    GPIO.cleanup()
