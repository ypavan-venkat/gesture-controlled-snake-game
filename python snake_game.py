import cv2
import mediapipe as mp
import pygame
import random
import sys
from collections import deque

# =============================
# MediaPipe Hand Detection
# =============================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# =============================
# Initialize Pygame
# =============================
pygame.init()
WIDTH, HEIGHT = 600, 400
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game - Finger Gesture Control")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)

# Snake Settings
snake_pos = [100, 50]
snake_body = [[100, 50], [90, 50], [80, 50]]
snake_direction = 'RIGHT'
change_to = snake_direction
speed = 15

# Food Settings
food_pos = [random.randrange(1, (WIDTH // 10)) * 10,
            random.randrange(1, (HEIGHT // 10)) * 10]
food_spawn = True

# FPS Controller
clock = pygame.time.Clock()

# Score
score = 0
font = pygame.font.SysFont('Arial', 24)

# =============================
# Finger Counting Function
# =============================
def count_fingers(hand_landmarks):
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    finger_count = 0

    # Thumb check (x axis)
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        finger_count += 1

    # Other fingers (y axis)
    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            finger_count += 1

    return finger_count

# =============================
# Gesture Smoothing
# =============================
gesture_buffer = deque(maxlen=5)  # last 5 frames

def get_smoothed_gesture(fingers):
    if fingers == 1:
        gesture_buffer.append("UP")
    elif fingers == 2:
        gesture_buffer.append("DOWN")
    elif fingers == 3:
        gesture_buffer.append("RIGHT")
    elif fingers >= 4:  # sometimes pinky is missed, so >=4
        gesture_buffer.append("LEFT")

    if len(gesture_buffer) == gesture_buffer.maxlen:
        # return most common gesture
        return max(set(gesture_buffer), key=gesture_buffer.count)
    return None

# =============================
# OpenCV Camera
# =============================
cap = cv2.VideoCapture(0)

while True:
    # ---- Handle Quit ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()

    # ---- OpenCV Processing ----
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            fingers = count_fingers(hand_landmarks)
            gesture = get_smoothed_gesture(fingers)

            if gesture:
                change_to = gesture

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Show detected gesture on screen
            cv2.putText(frame, f"Gesture: {gesture if gesture else 'Detecting...'}",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # ---- Update Snake Direction ----
    if change_to == 'UP' and not snake_direction == 'DOWN':
        snake_direction = 'UP'
    if change_to == 'DOWN' and not snake_direction == 'UP':
        snake_direction = 'DOWN'
    if change_to == 'LEFT' and not snake_direction == 'RIGHT':
        snake_direction = 'LEFT'
    if change_to == 'RIGHT' and not snake_direction == 'LEFT':
        snake_direction = 'RIGHT'

    # Move Snake with Wall Wrapping
    if snake_direction == 'UP':
        snake_pos[1] -= 10
    if snake_direction == 'DOWN':
        snake_pos[1] += 10
    if snake_direction == 'LEFT':
        snake_pos[0] -= 10
    if snake_direction == 'RIGHT':
        snake_pos[0] += 10

    # Wrap around screen
    snake_pos[0] = snake_pos[0] % WIDTH
    snake_pos[1] = snake_pos[1] % HEIGHT

    # Snake Growth
    snake_body.insert(0, list(snake_pos))
    if snake_pos[0] == food_pos[0] and snake_pos[1] == food_pos[1]:
        food_spawn = False
        score += 10
    else:
        snake_body.pop()

    if not food_spawn:
        food_pos = [random.randrange(1, (WIDTH // 10)) * 10,
                    random.randrange(1, (HEIGHT // 10)) * 10]
        food_spawn = True

    # Game Over (if snake bites itself)
    for block in snake_body[1:]:
        if snake_pos[0] == block[0] and snake_pos[1] == block[1]:
            pygame.quit()
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()

    # ---- Draw Everything ----
    win.fill(BLACK)
    for pos in snake_body:
        pygame.draw.rect(win, GREEN, pygame.Rect(pos[0], pos[1], 10, 10))

    pygame.draw.rect(win, RED, pygame.Rect(food_pos[0], food_pos[1], 10, 10))

    # Draw Score
    score_text = font.render(f"Score: {score}", True, WHITE)
    win.blit(score_text, [10, 10])

    pygame.display.update()
    clock.tick(speed)

    # ---- Show Camera ----
    cv2.imshow("Hand Gesture", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
