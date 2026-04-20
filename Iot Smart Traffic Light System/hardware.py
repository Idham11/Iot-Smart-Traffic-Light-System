import time
import threading
import os
import random

# Check if we're running on a Raspberry Pi
try:
    from gpiozero import LED, DigitalInputDevice
    MOCK_MODE = False
except ImportError:
    print("gpiozero not found. Running in MOCK mode.")
    MOCK_MODE = True

class TrafficLightController:
    def __init__(self):
        self.running = True
        self.lock = threading.Lock()
        
        self.lanes = {
            'A': {'light': 'red', 'count': 0, 'wait_time': 0, 'priority': 0},
            'B': {'light': 'red', 'count': 0, 'wait_time': 0, 'priority': 0},
            'C': {'light': 'red', 'count': 0, 'wait_time': 0, 'priority': 0}
        }
        
        self.active_lane = None
        
        # We will use callbacks to log decisions to app.py
        self.decision_callback = None

        if not MOCK_MODE:
            # GPIO Pin configurations for 3 lanes
            # Lane A
            self.led_A = {'red': LED(17), 'yellow': LED(27), 'green': LED(22)}
            self.radar_A = DigitalInputDevice(4)
            # Lane B
            self.led_B = {'red': LED(10), 'yellow': LED(9), 'green': LED(11)}
            self.radar_B = DigitalInputDevice(14)
            # Lane C
            self.led_C = {'red': LED(5), 'yellow': LED(6), 'green': LED(13)}
            self.radar_C = DigitalInputDevice(15)
        else:
            self.led_A = self.radar_A = None
            self.led_B = self.radar_B = None
            self.led_C = self.radar_C = None

        self.thread = threading.Thread(target=self._traffic_light_loop, daemon=True)
        self.thread.start()

    def set_decision_callback(self, callback):
        self.decision_callback = callback

    def _set_light(self, lane_id, color):
        with self.lock:
            self.lanes[lane_id]['light'] = color
            
        if not MOCK_MODE:
            leds = getattr(self, f"led_{lane_id}")
            leds['red'].off()
            leds['yellow'].off()
            leds['green'].off()
            if color in leds:
                leds[color].on()

    def _read_sensors(self):
        with self.lock:
            if not MOCK_MODE:
                # Basic presence accumulation logic could be more complex, 
                # but for simplicity we increment count if active
                if self.radar_A.is_active: self.lanes['A']['count'] += 1
                if self.radar_B.is_active: self.lanes['B']['count'] += 1
                if self.radar_C.is_active: self.lanes['C']['count'] += 1
            else:
                # Mock Mode: randomly adjust vehicle counts to simulate arriving/departing traffic
                for lane_id in self.lanes:
                    if random.random() < 0.3: # 30% chance a car arrives
                        self.lanes[lane_id]['count'] += 1
                    # If light is green, cars depart quickly
                    if self.lanes[lane_id]['light'] == 'green' and self.lanes[lane_id]['count'] > 0:
                        if random.random() < 0.8: # 80% chance car leaves per tick
                            self.lanes[lane_id]['count'] -= 1

    def _traffic_light_loop(self):
        # Initial state: All red
        for lane_id in self.lanes:
            self._set_light(lane_id, 'red')
            
        while self.running:
            self._read_sensors()
            
            with self.lock:
                # Calculate priorities
                candidates = []
                for lane_id, data in self.lanes.items():
                    if data['count'] > 0:
                        data['priority'] = (data['count'] * 2) + data['wait_time']
                        candidates.append((data['priority'], lane_id))
                    else:
                        data['priority'] = 0

                if not candidates:
                    # No vehicles anywhere, just wait
                    self.active_lane = None
                    time.sleep(1)
                    continue
                
                # Pick lane with max priority
                candidates.sort(reverse=True) # highest priority first
                best_priority, selected_lane = candidates[0]
                
                # Calculate green time
                count = self.lanes[selected_lane]['count']
                green_time = 10 + (count * 2)
                green_time = max(10, min(30, green_time)) # bound between 10 and 30
                
                reason = f"Highest priority {best_priority} with {count} vehicles."

            # Transition phase if changing lanes
            if self.active_lane and self.active_lane != selected_lane:
                self._set_light(self.active_lane, 'yellow')
                time.sleep(3)
                self._set_light(self.active_lane, 'red')
                # Increment wait times for the transition period
                with self.lock:
                    for l in self.lanes:
                        if l != selected_lane:
                            self.lanes[l]['wait_time'] += 3

            # Activate new lane
            self.active_lane = selected_lane
            self._set_light(selected_lane, 'green')
            
            # Log decision
            if self.decision_callback:
                counts = {l: self.lanes[l]['count'] for l in self.lanes}
                self.decision_callback(counts, selected_lane, best_priority, green_time, reason)
                
            # Green Phase execution
            elapsed = 0
            while elapsed < green_time and self.running:
                time.sleep(1)
                elapsed += 1
                self._read_sensors()
                
                # Update wait times for RED lanes
                with self.lock:
                    for lane_id in self.lanes:
                        if lane_id != selected_lane:
                            self.lanes[lane_id]['wait_time'] += 1
                    
                    # Reset wait time for active lane
                    self.lanes[selected_lane]['wait_time'] = 0

    def get_status(self):
        with self.lock:
            # Return a copy of the state
            return {
                "active_lane": self.active_lane,
                "lanes": {k: dict(v) for k, v in self.lanes.items()}
            }

    def stop(self):
        self.running = False
        if not MOCK_MODE:
            for l in ['A', 'B', 'C']:
                leds = getattr(self, f"led_{l}")
                leds['red'].off()
                leds['yellow'].off()
                leds['green'].off()

# Global instance
traffic_controller = TrafficLightController()

