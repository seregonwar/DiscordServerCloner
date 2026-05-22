import customtkinter as ctk
from typing import Callable
import math

class AnimationManager:
    @staticmethod
    def smooth_fade(widget: ctk.CTk, start: float, end: float, duration: int, on_complete: Callable = None):
        """
        Executes a smooth opacity transition
        """
        steps = 120  # Increased FPS for smoother animation
        step_time = duration / steps
        
        def animate(current_step=0):
            if current_step <= steps:
                progress = current_step / steps
                # Cubic easing function for more natural movement
                eased = progress * (2 - progress)
                current = start + (end - start) * eased
                
                widget.attributes('-alpha', current)
                widget.after(int(step_time), lambda: animate(current_step + 1))
            elif on_complete:
                on_complete()
                
        animate()
    
    @staticmethod
    def slide_in(widget: ctk.CTkFrame, direction: str = "right", duration: int = 200, on_complete: Callable = None):
        """
        Slides a widget into view with smooth movement
        """
        original_pos = widget.winfo_x(), widget.winfo_y()
        screen_width = widget.winfo_screenwidth()
        
        steps = 120  # Increased FPS
        step_time = duration / steps
        
        def animate(current_step=0):
            if current_step <= steps:
                progress = current_step / steps
                # Elastic easing function for more natural movement
                eased = 1 - math.pow(1 - progress, 5)
                
                if direction == "right":
                    current_x = screen_width - (screen_width - original_pos[0]) * eased
                    widget.place(x=current_x, y=original_pos[1])
                elif direction == "left":
                    current_x = -widget.winfo_width() + (original_pos[0] + widget.winfo_width()) * eased
                    widget.place(x=current_x, y=original_pos[1])
                elif direction == "top":
                    current_y = -widget.winfo_height() + (original_pos[1] + widget.winfo_height()) * eased
                    widget.place(x=original_pos[0], y=current_y)
                elif direction == "bottom":
                    screen_height = widget.winfo_screenheight()
                    current_y = screen_height - (screen_height - original_pos[1]) * eased
                    widget.place(x=original_pos[0], y=current_y)
                
                widget.after(int(step_time), lambda: animate(current_step + 1))
            elif on_complete:
                on_complete()
                
        animate()
    
    @staticmethod
    def slide_out(widget: ctk.CTkFrame, direction: str = "right", duration: int = 200, on_complete: Callable = None):
        """
        Slides a widget out of view with smooth movement
        """
        original_pos = widget.winfo_x(), widget.winfo_y()
        screen_width = widget.winfo_screenwidth()
        
        steps = 120  # Increased FPS
        step_time = duration / steps
        
        def animate(current_step=0):
            if current_step <= steps:
                progress = current_step / steps
                # Accelerated easing function for more natural exit
                eased = progress * progress
                
                if direction == "right":
                    current_x = original_pos[0] + (screen_width - original_pos[0]) * eased
                    widget.place(x=current_x, y=original_pos[1])
                elif direction == "left":
                    current_x = original_pos[0] - (original_pos[0] + widget.winfo_width()) * eased
                    widget.place(x=current_x, y=original_pos[1])
                elif direction == "top":
                    current_y = original_pos[1] - (original_pos[1] + widget.winfo_height()) * eased
                    widget.place(x=original_pos[0], y=current_y)
                elif direction == "bottom":
                    screen_height = widget.winfo_screenheight()
                    current_y = original_pos[1] + (screen_height - original_pos[1]) * eased
                    widget.place(x=original_pos[0], y=current_y)
                
                widget.after(int(step_time), lambda: animate(current_step + 1))
            elif on_complete:
                on_complete()
                
        animate()
    
    @staticmethod
    def pulse(widget, scale_start=1.0, scale_end=1.05, duration=500, repeat=False, on_complete: Callable = None):
        """
        Creates a gentle pulsing animation by scaling a widget
        """
        steps = 120
        step_time = duration / steps
        
        # Store original size
        original_width = widget.winfo_width()
        original_height = widget.winfo_height()
        
        def animate(current_step=0, direction=1):
            if current_step <= steps:
                progress = current_step / steps
                # Smooth sine easing
                eased = 0.5 - 0.5 * math.cos(progress * math.pi)
                
                if direction > 0:  # Scaling up
                    current_scale = scale_start + (scale_end - scale_start) * eased
                else:  # Scaling down
                    current_scale = scale_end - (scale_end - scale_start) * eased
                
                # Apply scaling
                new_width = int(original_width * current_scale)
                new_height = int(original_height * current_scale)
                
                # Calculate position to keep the widget centered
                x_offset = (new_width - original_width) // 2
                y_offset = (new_height - original_height) // 2
                
                # Configure the widget
                try:
                    widget.configure(width=new_width, height=new_height)
                except:
                    pass  # Some widgets might not support direct resizing
                
                widget.after(int(step_time), lambda: animate(current_step + 1, direction))
            else:
                if repeat:
                    # Reverse the direction and continue
                    animate(0, -direction)
                elif on_complete:
                    on_complete()
        
        animate()
    
    @staticmethod
    def blink(widget, color1, color2, duration=500, repeats=3, on_complete: Callable = None):
        """
        Creates a blinking animation by alternating colors
        """
        step_time = duration // 2  # Half for each color
        
        def animate(current_step=0):
            if current_step < repeats * 2:
                if current_step % 2 == 0:
                    widget.configure(fg_color=color2)
                else:
                    widget.configure(fg_color=color1)
                
                widget.after(step_time, lambda: animate(current_step + 1))
            else:
                # Return to original color
                widget.configure(fg_color=color1)
                if on_complete:
                    on_complete()
        
        animate()
    
    @staticmethod
    def sequential_reveal(widgets, delay=100, duration=300, direction="right"):
        """
        Reveals a sequence of widgets one after another with a delay
        """
        for i, widget in enumerate(widgets):
            # Hide initially
            widget.place_forget()
            
            # Schedule reveal with increasing delay
            widget.after(i * delay, lambda w=widget: AnimationManager.slide_in(w, direction, duration))