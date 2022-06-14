import threading
import time
import board
import adafruit_dht
import I2C_LCD_driver
import spidev
import RPi.GPIO as GPIO
from datetime import datetime
from time import sleep
# 라이브러리 import

pin = 17  # Input pin of sensor (GPIO.BOARD)
Buttons = [0x300ff629d, 0x300ffa857, 0x300ff22dd, 0x300ffc23d, 0x300ff02fd,0x300ff52ad]  # HEX code list , 리모컨 버튼 에 해당하는 값
ButtonsNames = ["UP",   "DOWN",      "LEFT",       "RIGHT",      "OK", "EXIT"]  # String list in same order as HEX list
# 0x300ff629d == UP
# 0x300ffa857 == DOWN
# 0x300ff22dd == LEFT
# 0x300ffc23d == RIGHT
# 0x300ff02fd == OK
# 0x300ff52ad == EXIT

# Sets up GPIO
GPIO.cleanup() # GPIO 핀 인식 에러로 인한 Clean up
GPIO.setmode(GPIO.BCM) #GPIO Number 를 통한 회로도 구성
GPIO.setup(pin, GPIO.IN) #17번 리모컨 제어 및 IR

GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT) #LED 26번 GPIO사용 , Water Level 경고등

roop_while = True # 반복문 제어 변수
while_in = False # 반복문 제어 변수

#Servo
servo_pin = 21 # Servo Motor GPIO 21번 핀 사용

GPIO.setup(servo_pin,GPIO.OUT)

# Gets binary value
motor_degree = 0 # 모터 각도 초기 기본값 0으로 세팅
Auto_stop = True # 무한반복문 제어 변수

mylcd = I2C_LCD_driver.lcd()

dhtDevice = adafruit_dht.DHT11(board.D18) #DHT GPIO 18번 핀 사용

GPIO.setup(23, GPIO.IN) # 수위센서 GPIO 23번 핀 사용



def getBinary():
    # Internal vars
    num1s = 0  # Number of consecutive 1s read
    binary = 1  # The binary value
    command = []  # The list to store pulse times in
    previousValue = 0  # The last value
    value = GPIO.input(pin)  # The current value

	# Waits for the sensor to pull pin low
    while value:
        sleep(0.0001)# This sleep decreases CPU utilization immensely
        value = GPIO.input(pin)
		
	# Records start time
    startTime = datetime.now() #현재 시간
	
    while True:
		# If change detected in value
        if previousValue != value:
            now = datetime.now()
            pulseTime = now - startTime #Calculate the time of pulse
            startTime = now #Reset start time
            command.append((previousValue, pulseTime.microseconds)) #Store recorded data
			
		# Updates consecutive 1s variable
        if value:
            num1s += 1
        else:
            num1s = 0
		
		# Breaks program when the amount of 1s surpasses 10000
        if num1s > 10000:
            break
			
		# Re-reads pin
        previousValue = value
        value = GPIO.input(pin)
	
	# Converts times to binary
    for (typ, tme) in command:
        if typ == 1: #If looking at rest period
            if tme > 1000: #If pulse greater than 1000us
                binary = binary *10 +1 #Must be 1
            else:
                binary *= 10 #Must be 0
			
    if len(str(binary)) > 34: #Sometimes, there is some stray characters
        binary = int(str(binary)[:34])
		
    return binary


# Convert value to hex
def convertHex(binaryValue):
    tmpB2 = int(str(binaryValue),2) #Temporarely propper base 2
    return hex(tmpB2)
    
def Up_Servor():
    
    global motor_degree #전역변수 모터 각도 
    print("UP!!")
    
    pwm = GPIO.PWM(servo_pin, 50)
    pwm.start(motor_degree)
    
    
    if(motor_degree != 60):
        for high_time in range (motor_degree,60):
            pwm.ChangeDutyCycle(high_time/10.0) # for 반복문에 실수가 올 수 없으므로 /10.0 로 처리함. 
            time.sleep(0.02)
        motor_degree = 60
        
    #pwm.ChangeDutyCycle(3.0)    
    time.sleep(1.0)
    
def Down_Servor():
    
    global motor_degree #전역변수 모터 각도 
    print("Down!!")
    
    pwm = GPIO.PWM(servo_pin, 50)
    pwm.start(motor_degree)
    
    
    if(motor_degree > 20):
        for high_time in range (motor_degree,20,-1):
            pwm.ChangeDutyCycle(high_time/10.0) # for 반복문에 실수가 올 수 없으므로 /10.0 로 처리함. 
            time.sleep(0.02)
        motor_degree = 20
        
    #pwm.ChangeDutyCycle(3.0)    
    time.sleep(1.0)
    
def Reset_Servor():
    
    global motor_degree #전역변수 모터 각도 
    print("Reset!!")
    
    pwm = GPIO.PWM(servo_pin, 50) # Servo Motor 기본설정
    pwm.start(motor_degree) # Servo Motor 기본설정
    
    
    if(motor_degree != 40): # reset 각도가 아니라면 조건문 작용
        if(motor_degree > 40): # reset 각도보다 크다면 reset 각도에 맞춰서 변화
            for high_time in range (motor_degree,40,-1):
                pwm.ChangeDutyCycle(high_time/10.0) # for 반복문에 실수가 올 수 없으므로 /10.0 로 처리함. 
                time.sleep(0.02)
        else: # reset 각도보다 작다면 reset 각도에 맞춰서 변화
            for high_time in range (motor_degree,40): 
                pwm.ChangeDutyCycle(high_time/10.0) # for 반복문에 실수가 올 수 없으므로 /10.0 로 처리함. 
                time.sleep(0.02)
        motor_degree = 40
 
    time.sleep(1.0)



def print_LCD():
    global input
    while True:
        try:
            
            temperature_c = dhtDevice.temperature # 섭씨 온도 확인
            temperature_f = temperature_c * (9/5)+32 # 화씨 온도 확인

            humidity = dhtDevice.humidity
        
            mylcd.lcd_display_string(f"Smart Humidifier",1) # LCD 첫째줄 문자열 출력
            mylcd.lcd_display_string(f"Temperature : {temperature_c}",2) # LCD 둘째줄 섭씨온도 출력
            mylcd.lcd_display_string(f"Humidity : {humidity}%",3) # LCD 세번째 줄 습도 출력
            
            
            input = GPIO.input(23) # Water level 센서 GPIO 출력값 받아주기
            
            if(input == 0): # input 이 0이라면 현재 물부족 상태
                mylcd.lcd_display_string(f"Water Level Low",4) # 사용자에게 메시지 출력 LCD 네번째 줄
                GPIO.output(26,GPIO.HIGH) # 물 상태를 사용자에게 알려주는 LED 경고등 점등
                time.sleep(2)
            elif(input == 1):
                mylcd.lcd_display_string(f"Plenty of water",4) # 사용자에게 메시지 출력 LCD 네번째 줄
                GPIO.output(26,GPIO.LOW) # 물 상태를 사용자에게 알려주는 LED 경고등 점등상태 해제
                time.sleep(2)
        
            time.sleep(2.0)
        except : #ERROR 확인
            print(f"input : {input}") 
            print("error")
            pass #error 가 발생해도 무한반복


    
def IR_Servo():
    global roop_while, inData ,while_in
    Reset_Servor() # 초기 각도 reset 함수로 세팅 
    while True:

        inData = convertHex(getBinary()) #Runs subs to get incoming hex value

        if(inData == "0x300ff629d"): # 리모컨 상단 버튼 을 통한 Servo Motor 함수 호출
            print("Up(Rotation) press")
            Up_Servor()
        
        elif(inData == "0x300ffa857"): # 리모컨 하단 버튼 을 통한 Servo Motor 함수 호출
            print("Down(Rotation) press")
            Down_Servor()
        
        elif(inData == "0x300ff22dd"): # 리모컨 좌측 버튼 을 통한 Servo Motor 함수 호출
            print("while(Rotation) press")
            while(roop_while):
                while_in = True
                Up_Servor()  
                Down_Servor()
            Reset_Servor()
            roop_while = True
        
        elif(inData == "0x300ffc23d"): # 리모컨 우측 버튼 을 통한 Servo Motor 함수 호출
            print("Right(Reset) press")
            Reset_Servor()

	
        for button in range(len(Buttons)):#Runs through every value in list
            if (hex(Buttons[button]) == inData): #Checks this against incoming
                
                print(ButtonsNames[button]) #Prints corresponding english name for button
    
        
    
threading.Thread(target=print_LCD).start() # LCD , 습도 , 수위센서 , LED 쓰레드1
threading.Thread(target=IR_Servo).start()  # IR 센서 , 리모컨 , LED 쓰레드2

