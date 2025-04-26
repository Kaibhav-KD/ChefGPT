import google.generativeai as genai
from datetime import datetime
import os
import re
import requests
import json
from langdetect import detect
import regex  # For better Unicode support
import colorama
from colorama import Fore, Back, Style
import speech_recognition as sr
import tkinter as tk
from tkinter import ttk
import threading
import pygame
import time

# Initialize colorama for Windows systems
colorama.init()

# Initialize pygame for sound effects
pygame.mixer.init()

GOOGLE_API_KEY = "AIzaSyDqoKhqwJvcXlkt2kDXG8375WlSCkJLYXs"
NUTRITION_API_KEY = "7d6e3e97c3msh3af1c32a3c0f2f3p1c7925jsn3ce9f7eac63d"  # Replace with your API key

# ASCII Art Logo
CHEFGPT_LOGO = """
    ██████╗██╗  ██╗███████╗███████╗ ██████╗ ██████╗ ████████╗
   ██╔════╝██║  ██║██╔════╝██╔════╝██╔════╝ ██╔══██╗╚══██╔══╝
   ██║     ███████║█████╗  █████╗  ██║  ███╗██████╔╝   ██║   
   ██║     ██╔══██║██╔══╝  ██╔══╝  ██║   ██║██╔═══╝    ██║   
   ╚██████╗██║  ██║███████╗██║     ╚██████╔╝██║        ██║   
    ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝        ╚═╝   
                    🔪 ChefGPT - Cooking Reimagined 👨‍🍳
"""

# Project information
PROJECT_NAME = "ChefGPT"
PROJECT_VERSION = "1.0.0"
PROJECT_DESCRIPTION = "ChefGPT - Your intelligent cooking companion powered by AI"

genai.configure(api_key=GOOGLE_API_KEY)


generation_config = {
    "temperature": 0.7,  # Controls creativity in recipe suggestions
    "top_p": 0.8,       # Controls diversity of responses
    "top_k": 40,        # Controls diversity of responses
    "max_output_tokens": 2048,  # Maximum length of response
}


safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]


system_instructions = """
Welcome to ChefGPT - Where AI meets culinary excellence!

You are ChefGPT, a state-of-the-art culinary AI that combines traditional cooking wisdom with modern technology. Your responses should be:

1. Recipe Format:
   • Detailed recipe instructions with exact measurements
   • Step-by-step cooking method with timing
   • Proper ingredient list with quantities
   • Cooking tips and techniques
   • Time management suggestions

2. Nutrition Analysis:
   • Calculate and display complete nutritional information
   • Break down macronutrients (proteins, carbs, fats)
   • List micronutrients (vitamins, minerals)
   • Provide daily value percentages
   • Highlight health benefits of ingredients

3. Health Considerations:
   • Mention allergen information
   • Suggest healthy substitutions
   • Provide calorie information
   • Note dietary restrictions (vegan, gluten-free, etc.)
   • Include portion size recommendations

4. Format all responses in this structure:
   〈Recipe Name〉
   ━━━━━━━━━━━━━━━━━━━━━━

   ⏱️ Taiyari ka Time
   ━━━━━━━━━━━━━━━━
   [Preparation details]

   🥘 Ingredients
   ━━━━━━━━━━━
   [Ingredient list]

   📝 Banane ka Tarika
   ━━━━━━━━━━━━━━━━
   [Step by step instructions]

   💡 Kuch Zaroori Tips
   ━━━━━━━━━━━━━━━━
   [Important tips]

   ⚡ Time Management ke Tips
   ━━━━━━━━━━━━━━━━━━━━━━
   [Time management advice]

   📊 Poshan ki Jaankari
   ━━━━━━━━━━━━━━━━━━
   [Complete nutrition analysis]

5. Language Adaptation:
   • Use Hinglish for Hinglish queries
   • Use English for English queries
   • Maintain formatting in both languages

Always maintain the ChefGPT brand voice: professional, innovative, and approachable."""


model = genai.GenerativeModel(
    "gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=system_instructions
)

def get_time_based_greeting():
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 22:
        return "Good evening"
    else:
        return "Good night"

def log_conversation(user_name, user_input, bot_response):
   
    if not os.path.exists('chatlogs'):
        os.makedirs('chatlogs')
    
   
    log_file = f'chatlogs/chat_{datetime.now().strftime("%Y-%m-%d")}.txt'
    
   
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n[{timestamp}]\n{user_name}: {user_input}\nChef AI: {bot_response}\n"
    
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def get_nutrition_info(recipe_name, ingredients):
    """Get nutrition information for a recipe using Nutrition API"""
    try:
        url = "https://nutrition-by-api-ninjas.p.rapidapi.com/v1/nutrition"
        headers = {
            "X-RapidAPI-Key": NUTRITION_API_KEY,
            "X-RapidAPI-Host": "nutrition-by-api-ninjas.p.rapidapi.com"
        }
        
        total_nutrition = {
            'calories': 0,
            'protein_g': 0,
            'carbohydrates_total_g': 0,
            'fat_total_g': 0,
            'saturated_fat_g': 0,
            'cholesterol_mg': 0,
            'fiber_g': 0,
            'sugar_g': 0,
            'sodium_mg': 0,
            'potassium_mg': 0,
            'iron_mg': 0,
            'vitamin_c_mg': 0,
            'calcium_mg': 0,
            'vitamin_a_iu': 0,
            'vitamin_d_iu': 0
        }
        
        # Query each ingredient separately for more accurate results
        for ingredient in ingredients:
            params = {"query": ingredient}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    nutrition = data[0]
                    # Sum up all nutritional values
                    for key in total_nutrition:
                        total_nutrition[key] += float(nutrition.get(key, 0))
        
        # Format the nutrition information with proper spacing and styling
        return f"""
                    📊 Poshan ki Jaankari (Nutrition Analysis)
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    🔥 Calories aur Macronutrients
                    ━━━━━━━━━━━━━━━━━━━━━━━━
                    • Total Calories: {round(total_nutrition['calories'])} kcal
                    • Protein: {round(total_nutrition['protein_g'], 1)}g
                    • Carbohydrates: {round(total_nutrition['carbohydrates_total_g'], 1)}g
                    • Total Fat: {round(total_nutrition['fat_total_g'], 1)}g
                    • Saturated Fat: {round(total_nutrition['saturated_fat_g'], 1)}g
                    • Fiber: {round(total_nutrition['fiber_g'], 1)}g
                    • Sugar: {round(total_nutrition['sugar_g'], 1)}g

                    ❤️ Heart Health
                    ━━━━━━━━━━━
                    • Cholesterol: {round(total_nutrition['cholesterol_mg'])}mg
                    • Sodium: {round(total_nutrition['sodium_mg'])}mg
                    • Potassium: {round(total_nutrition['potassium_mg'])}mg

                    🦴 Minerals aur Vitamins
                    ━━━━━━━━━━━━━━━━━━
                    • Iron: {round(total_nutrition['iron_mg'], 1)}mg
                    • Calcium: {round(total_nutrition['calcium_mg'])}mg
                    • Vitamin C: {round(total_nutrition['vitamin_c_mg'])}mg
                    • Vitamin A: {round(total_nutrition['vitamin_a_iu'])} IU
                    • Vitamin D: {round(total_nutrition['vitamin_d_iu'])} IU

                    💡 Daily Values ke hisaab se (2000 calorie diet)
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    • Protein: {round((total_nutrition['protein_g'] / 50) * 100)}% daily value
                    • Carbs: {round((total_nutrition['carbohydrates_total_g'] / 300) * 100)}% daily value
                    • Fat: {round((total_nutrition['fat_total_g'] / 65) * 100)}% daily value
                    • Fiber: {round((total_nutrition['fiber_g'] / 25) * 100)}% daily value
                    • Iron: {round((total_nutrition['iron_mg'] / 18) * 100)}% daily value
                    • Calcium: {round((total_nutrition['calcium_mg'] / 1000) * 100)}% daily value

                    📝 Note
                    ━━━━━
                    • Ye value approximate hain aur actual ingredients ke hisaab se vary kar sakti hain
                    • Daily values 2000 calorie diet ke hisaab se calculate ki gayi hain
                    • Portion size ke hisaab se nutrition values change ho sakti hain"""

    except Exception as e:
        print(f"Error fetching nutrition info: {e}")
        return ""

class Chatbot:
    def __init__(self, api_key):
        """Initialize the chatbot with the API key and configure the model"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            "gemini-1.5-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        self.chat_session = self.model.start_chat(history=[])
        self._setup_prompt_template()

    def _setup_prompt_template(self):
        """Set up the system prompt template for consistent formatting"""
        self.system_prompt = """You are Chef AI, a professional chef and nutritionist with extensive knowledge of global cuisines, cooking techniques, and nutrition science. Your responses should be:

1. Recipe Format:
   • Detailed recipe instructions with exact measurements
   • Step-by-step cooking method with timing
   • Proper ingredient list with quantities
   • Cooking tips and techniques
   • Time management suggestions

2. Nutrition Analysis:
   • Calculate and display complete nutritional information
   • Break down macronutrients (proteins, carbs, fats)
   • List micronutrients (vitamins, minerals)
   • Provide daily value percentages
   • Highlight health benefits of ingredients

3. Health Considerations:
   • Mention allergen information
   • Suggest healthy substitutions
   • Provide calorie information
   • Note dietary restrictions (vegan, gluten-free, etc.)
   • Include portion size recommendations

4. Format all responses in this structure:
   〈Recipe Name〉
   ━━━━━━━━━━━━━━━━━━━━━━

   ⏱️ Taiyari ka Time
   ━━━━━━━━━━━━━━━━
   [Preparation details]

   🥘 Ingredients
   ━━━━━━━━━━━
   [Ingredient list]

   📝 Banane ka Tarika
   ━━━━━━━━━━━━━━━━
   [Step by step instructions]

   💡 Kuch Zaroori Tips
   ━━━━━━━━━━━━━━━━
   [Important tips]

   ⚡ Time Management ke Tips
   ━━━━━━━━━━━━━━━━━━━━━━
   [Time management advice]

   📊 Poshan ki Jaankari
   ━━━━━━━━━━━━━━━━━━
   [Complete nutrition analysis]

5. Language Adaptation:
   • Use Hinglish for Hinglish queries
   • Use English for English queries
   • Maintain formatting in both languages

Always maintain professional yet approachable tone and be ready to help with any culinary query."""

    def _format_recipe(self, text):
        """Format recipe text with beautiful styling"""
        # Replace bullet points and asterisks with elegant bullets
        text = re.sub(r'[*•]', '•', text)
        
        # Extract ingredients for nutrition calculation
        ingredients = []
        ingredients_match = re.findall(r'•\s*([^•\n]+)', text)
        if ingredients_match:
            ingredients = [ing.strip() for ing in ingredients_match]
        
        # Add decorative header for recipe name
        if "Recipe:" in text:
            text = text.replace("Recipe:", "")
        recipe_match = re.search(r'(.+?)(?:\n|$)', text)
        if recipe_match:
            recipe_name = recipe_match.group(1).strip()
            text = f"""
                        〈{recipe_name}〉
                    ━━━━━━━━━━━━━━━━━━━━━━

                    ⏱️ Taiyari ka Time
                    ━━━━━━━━━━━━━━━━

                    • Preparation Time: [time] minute
                    • Cooking Time: [time] minute
                    • Total Time: [time] minute
                    • Level: [Easy/Medium/Hard]

                    🥘 Ingredients
                    ━━━━━━━━━━━

                    • [quantity] [ingredient 1]
                    • [quantity] [ingredient 2]
                    • [quantity] [ingredient 3]

                    📝 Banane ka Tarika
                    ━━━━━━━━━━━━━━━━

                    1. [First step] ([time] minute)
                       ➜ [Additional details]

                    2. [Second step] ([time] minute)
                       ➜ [Additional details]

                    3. [Third step] ([time] minute)
                       ➜ [Additional details]

                    💡 Kuch Zaroori Tips
                    ━━━━━━━━━━━━━━━━

                    • [Important tip 1]
                    • [Important tip 2]
                    • [Important tip 3]

                    ⚡ Time Management ke Tips
                    ━━━━━━━━━━━━━━━━━━━━━━

                    • Pehle se kya taiyar kar sakte hain
                    • Kaun se steps ek saath kar sakte hain
                    • Time kaise bacha sakte hain

""" + text[len(recipe_match.group(0)):]
        
        # Format sections with extra spacing and decorative elements
        sections = {
            "Time Required:": "\n                    ⏱️ Taiyari ka Time\n                    ━━━━━━━━━━━━━━━━\n",
            "Prep Time:": "• Preparation Time:",
            "Cook Time:": "• Cooking Time:",
            "Total Time:": "• Total Time:",
            "Difficulty Level:": "• Level:",
            "Ingredients:": "\n                    🥘 Ingredients\n                    ━━━━━━━━━━━\n",
            "Instructions:": "\n                    📝 Banane ka Tarika\n                    ━━━━━━━━━━━━━━━━\n",
            "Steps:": "\n                    📝 Steps\n                    ━━━━━━━\n",
            "Tips:": "\n                    💡 Kuch Zaroori Tips\n                    ━━━━━━━━━━━━━━━━\n",
            "Note:": "\n                    📌 Note\n                    ━━━━━━\n",
            "Quick Tips:": "\n                    ⚡ Time Management ke Tips\n                    ━━━━━━━━━━━━━━━━━━━━━━\n"
        }
        
        for old, new in sections.items():
            text = text.replace(old, new)
        
        # Format numbered steps with proper spacing, timing, and indentation
        text = re.sub(r'(\d+)\.\s*(.*?)(\[.*?\])', r'                    \1. \2 ⏱️\3', text)
        
        # Add arrow and indent for step details
        text = re.sub(r'\n\s+([A-Za-z])', r'\n                       ➜ \1', text)
        
        # Format ingredient list with proper spacing and bullets
        ingredients_section = re.search(r'🥘 Ingredients\n                    ━━━━━━━━━━━\n(.*?)(?=\n\n)', text, re.DOTALL)
        if ingredients_section:
            ingredients_text = ingredients_section.group(1)
            formatted_ingredients = "\n".join(
                f"                    • {line.strip().strip('•').strip()}"
                for line in ingredients_text.split('\n')
                if line.strip()
            )
            text = text.replace(ingredients_section.group(1), f"\n{formatted_ingredients}\n")
            
            # Update ingredients list for nutrition calculation
            ingredients = [
                line.strip().strip('•').strip()
                for line in ingredients_text.split('\n')
                if line.strip()
            ]
        
        # Format tips with proper indentation
        tips_section = re.search(r'💡 Kuch Zaroori Tips\n                    ━━━━━━━━━━━━━━━━\n(.*?)(?=\n\n|$)', text, re.DOTALL)
        if tips_section:
            tips_text = tips_section.group(1)
            formatted_tips = "\n".join(
                f"                    • {line.strip().strip('•').strip()}"
                for line in tips_text.split('\n')
                if line.strip()
            )
            text = text.replace(tips_section.group(1), f"\n{formatted_tips}\n")
        
        # Always add nutrition information at the end
        if recipe_match:
            recipe_name = recipe_match.group(1).strip()
            nutrition_info = get_nutrition_info(recipe_name, ingredients)
            if nutrition_info:
                text += f"\n{nutrition_info}"
        
        # Add final decorative footer with proper alignment
        text += "\n                    ━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return text.strip()

    def _format_general_response(self, text):
        """Format general responses with beautiful styling"""
        # Replace bullet points with elegant bullets
        text = re.sub(r'[*•]', '•', text)
        
        # Add spacing between points
        text = re.sub(r'(•.*?)(\n•)', r'\1\n\n•', text)
        
        # Format important points with spacing
        text = re.sub(r'Important:', '\n\n💡 Important:\n', text)
        text = re.sub(r'Note:', '\n\n📌 Note:\n', text)
        
        # Add spacing for readability
        text = re.sub(r'([.!?])\s+', r'\1\n\n', text)
        
        # Clean up multiple blank lines
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()

    def get_response(self, user_input):
        """Get a beautifully formatted response from the chatbot"""
        try:
            # Detect if input is Hinglish
            is_input_hinglish = is_hinglish(user_input)
            
            # Analyze input for recipe/ingredient keywords
            recipe_keywords = ['recipe', 'banao', 'kaise banate', 'how to make', 'बनाओ', 'रेसिपी']
            ingredient_keywords = ['with', 'using', 'से', 'के साथ', 'ingredients']
            
            # Construct enhanced prompt based on input type
            if any(keyword in user_input.lower() for keyword in recipe_keywords):
                # Recipe request
                enhanced_prompt = f"""Please provide a detailed recipe with complete nutritional analysis for: {user_input}

Include:
1. Exact measurements and portions
2. Step-by-step instructions with timing
3. Complete nutritional breakdown including:
   - Calories and macronutrients
   - Vitamins and minerals
   - Daily value percentages
   - Health benefits
4. Cooking tips and techniques
5. Time management suggestions

Format the response according to the template with proper sections and formatting."""

            elif any(keyword in user_input.lower() for keyword in ingredient_keywords):
                # Ingredient-based request
                enhanced_prompt = f"""Create a recipe using the mentioned ingredients: {user_input}

Include:
1. Creative recipe suggestions
2. Complete nutritional analysis of ingredients
3. Health benefits of each ingredient
4. Possible substitutions
5. Dietary considerations

Format the response with all sections including nutrition information."""

            else:
                # General cooking query
                enhanced_prompt = f"{self.system_prompt}\n\nUser: {user_input}"

            # Get response from model
            response = self.chat_session.send_message(enhanced_prompt).text
            
            # Format based on content type
            if any(keyword in user_input.lower() for keyword in recipe_keywords + ingredient_keywords):
                formatted_response = self._format_recipe(response)
            else:
                formatted_response = self._format_general_response(response)
            
            # Convert to Hinglish if input was Hinglish
            if is_input_hinglish:
                formatted_response = format_hinglish_response(formatted_response)
            
            return formatted_response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

    def reset_chat(self):
        """Reset the chat session"""
        self.chat_session = self.model.start_chat(history=[])


def is_hinglish(text):
    """
    Detect if the text is Hinglish (mix of Hindi written in English and English)
    """
    # Common Hinglish words and patterns
    hinglish_patterns = [
        r'kya', r'hai', r'kaise', r'acha', r'thik', r'nahi',
        r'matlab', r'bahut', r'aur', r'main', r'haan', r'naa',
        r'karna', r'banana', r'khana', r'recipe', r'banao',
        r'chahiye', r'batao', r'karo', r'do', r'bolo'
    ]
    
    # Convert text to lowercase for better matching
    text_lower = text.lower()
    
    # Check for Hinglish patterns
    matches = sum(1 for pattern in hinglish_patterns if re.search(rf'\b{pattern}\b', text_lower))
    
    # If more than 1 Hinglish pattern is found, consider it Hinglish
    return matches > 1

def translate_cooking_terms_to_hinglish(text):
    """
    Replace common cooking terms with their Hinglish equivalents
    """
    cooking_terms = {
        'minutes': 'minute',
        'hours': 'ghante',
        'cook': 'pakayein',
        'heat': 'garam karein',
        'cut': 'kaat lein',
        'mix': 'mix kar lein',
        'add': 'daal dein',
        'stir': 'chalayein',
        'boil': 'ubalein',
        'fry': 'fry karein',
        'bake': 'bake karein',
        'ingredients': 'ingredients',
        'recipe': 'recipe',
        'preparation': 'taiyari',
        'instructions': 'instructions',
        'steps': 'steps',
        'tips': 'tips',
        'note': 'note',
        'time required': 'time lagega',
        'prep time': 'taiyari ka time',
        'cook time': 'pakane ka time',
        'total time': 'total time',
        'serving': 'serving',
        'difficulty level': 'difficulty level'
    }
    
    for eng, hing in cooking_terms.items():
        text = re.sub(rf'\b{eng}\b', hing, text, flags=re.IGNORECASE)
    
    return text

def format_hinglish_response(text):
    """
    Format the response in Hinglish style
    """
    # First translate common cooking terms
    text = translate_cooking_terms_to_hinglish(text)
    
    # Add Hinglish style greetings and phrases
    text = text.replace("Here's your recipe:", "Ye rahi aapki recipe:")
    text = text.replace("Instructions:", "Recipe banane ka tarika:")
    text = text.replace("Tips:", "Kuch zaroori tips:")
    text = text.replace("Note:", "Dhyan rakhein:")
    text = text.replace("Nutrition Analysis", "Poshan ki jaankari")
    
    return text

class VoiceInput:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        
        # Configure silence detection parameters
        self.recognizer.pause_threshold = 1.0  # Seconds of silence to stop
        self.recognizer.energy_threshold = 300  # Minimum audio energy to consider as speech
        self.recognizer.dynamic_energy_threshold = True  # Automatically adjust for ambient noise
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        
        # Load sound effects
        try:
            pygame.mixer.Sound("start_listening.wav")
            pygame.mixer.Sound("stop_listening.wav")
        except:
            print("Sound effects not found. Continuing without sound.")
    
    def play_sound(self, sound_type):
        try:
            if sound_type == "start":
                pygame.mixer.Sound("start_listening.wav").play()
            elif sound_type == "stop":
                pygame.mixer.Sound("stop_listening.wav").play()
        except:
            pass
    
    def listen(self):
        with sr.Microphone() as source:
            print(f"\n{Fore.YELLOW}🎤 Listening...{Style.RESET_ALL}")
            self.play_sound("start")
            
            # Adjust for ambient noise
            print(f"{Fore.YELLOW}🔊 Adjusting for background noise...{Style.RESET_ALL}")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            try:
                # Listen for audio input with automatic silence detection
                print(f"{Fore.GREEN}🎙️ Speak now! (Will auto-stop after 1 second of silence){Style.RESET_ALL}")
                audio = self.recognizer.listen(source, 
                                            timeout=None,  # No timeout for starting speech
                                            phrase_time_limit=None)  # No limit on phrase length
                
                self.play_sound("stop")
                print(f"{Fore.YELLOW}🔄 Processing your voice...{Style.RESET_ALL}")
                
                # Convert speech to text using both Hindi and English recognition
                try:
                    # Try Hindi first
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                except:
                    try:
                        # If Hindi fails, try English
                        text = self.recognizer.recognize_google(audio, language='en-IN')
                    except:
                        # If both fail, try without language specification
                        text = self.recognizer.recognize_google(audio)
                
                print(f"{Fore.GREEN}✓ Recognized: {text}{Style.RESET_ALL}")
                return text
                
            except sr.WaitTimeoutError:
                self.play_sound("stop")
                print(f"{Fore.RED}⚠️ No speech detected{Style.RESET_ALL}")
                return None
            except sr.UnknownValueError:
                self.play_sound("stop")
                print(f"{Fore.RED}⚠️ Could not understand audio{Style.RESET_ALL}")
                return None
            except sr.RequestError as e:
                self.play_sound("stop")
                print(f"{Fore.RED}⚠️ Could not request results; {e}{Style.RESET_ALL}")
                return None
            except Exception as e:
                self.play_sound("stop")
                print(f"{Fore.RED}⚠️ Error: {e}{Style.RESET_ALL}")
                return None

class ChatbotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{PROJECT_NAME} v{PROJECT_VERSION}")
        self.root.geometry("800x600")
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap("chefgpt_icon.ico")
        except:
            pass
        
        # Configure style with ChefGPT theme colors
        style = ttk.Style()
        style.configure("ChefGPT.TFrame", background="#f5f5f5")
        style.configure("ChefGPT.TButton", padding=10, font=('Helvetica', 12))
        style.configure("ChefGPT.TLabel", font=('Helvetica', 10))
        style.configure("Recording.TButton", padding=10, font=('Helvetica', 12), foreground='red')
        
        # Create main frame with ChefGPT styling
        self.main_frame = ttk.Frame(self.root, padding="10", style="ChefGPT.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with project info
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text=PROJECT_DESCRIPTION, style="ChefGPT.TLabel").pack()
        
        # Create chat display with ChefGPT styling
        self.chat_display = tk.Text(
            self.main_frame,
            wrap=tk.WORD,
            font=('Helvetica', 10),
            bg="#ffffff",
            fg="#333333"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar to chat display
        scrollbar = ttk.Scrollbar(self.chat_display)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.chat_display.yview)
        
        # Create input frame with ChefGPT styling
        self.input_frame = ttk.Frame(self.main_frame, style="ChefGPT.TFrame")
        self.input_frame.pack(fill=tk.X, pady=5)
        
        # Create text input with ChefGPT styling
        self.text_input = ttk.Entry(
            self.input_frame,
            font=('Helvetica', 10),
            style="ChefGPT.TEntry"
        )
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Create voice input button with ChefGPT styling
        self.voice_button = ttk.Button(
            self.input_frame,
            text="🎤",
            style="ChefGPT.TButton",
            command=self.toggle_voice_input
        )
        self.voice_button.pack(side=tk.RIGHT)
        
        # Create send button with ChefGPT styling
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            style="ChefGPT.TButton",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        # Create status label with ChefGPT styling
        self.status_label = ttk.Label(
            self.input_frame,
            text="",
            font=('Helvetica', 9),
            style="ChefGPT.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Initialize voice input
        self.voice_input = VoiceInput()
        self.is_listening = False
        
        # Bind enter key to send message
        self.text_input.bind('<Return>', lambda e: self.send_message())
        
        # Initialize chat session
        self.chat_session = model.start_chat(history=[])
        
        # Display welcome message with ChefGPT branding
        self.display_message("ChefGPT", CHEFGPT_LOGO, "system")
        self.display_message(
            "ChefGPT",
            f"Welcome to {PROJECT_NAME} v{PROJECT_VERSION}!\n" +
            "Namaste! Main aapka culinary AI companion hoon!\n" +
            "Aap mujhse kisi bhi recipe ke baare mein pooch sakte hain 👨‍🍳\n",
            "bot"
        )
    
    def toggle_voice_input(self):
        if not self.is_listening:
            self.is_listening = True
            self.voice_button.configure(text="🔴", style="Recording.TButton")
            self.status_label.configure(text="Listening... (Will auto-stop after silence)")
            threading.Thread(target=self.process_voice_input).start()
        else:
            self.is_listening = False
            self.voice_button.configure(text="🎤", style="Mic.TButton")
            self.status_label.configure(text="")
    
    def process_voice_input(self):
        text = self.voice_input.listen()
        if text:
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, text)
            self.send_message()
        self.is_listening = False
        self.voice_button.configure(text="🎤", style="Mic.TButton")
        self.status_label.configure(text="")
    
    def display_message(self, sender, message, message_type="user"):
        self.chat_display.configure(state='normal')
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] ")
        
        # Format based on message type
        if message_type == "system":
            self.chat_display.insert(tk.END, message + "\n")
        elif message_type == "user":
            self.chat_display.insert(tk.END, f"🧑 You: {message}\n")
        elif message_type == "bot":
            self.chat_display.insert(tk.END, f"👨‍🍳 ChefGPT: {message}\n")
        elif message_type == "error":
            self.chat_display.insert(tk.END, f"⚠️ Error: {message}\n")
        
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)
        
    def send_message(self):
        user_input = self.text_input.get().strip()
        if user_input:
            # Display user message
            self.display_message("You", user_input, "user")
            
            try:
                # Get bot response
                response = self.chat_session.send_message(user_input)
                bot_response = response.text.strip()
                
                # Format response in Hinglish if input was Hinglish
                if is_hinglish(user_input):
                    bot_response = format_hinglish_response(bot_response)
                
                # Display bot response
                self.display_message("ChefGPT", bot_response, "bot")
                
                # Clear input field
                self.text_input.delete(0, tk.END)
                
            except Exception as e:
                self.display_message("Error", str(e), "error")
    
    def run(self):
        self.root.mainloop()

def main():
    app = ChatbotGUI()
    app.run()

if __name__ == "__main__":
    main()
