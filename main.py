#!/usr/bin/env python3

import sys
from services.command_processor import CommandProcessor


def print_banner():
    print(r"""
 _   _                         _____ _      _____ 
| | | |_   _ _ __   ___ _ __ / ____| |    |_   _|
| |_| | | | | '_ \ / _ \ '__| |    | |      | |  
|  _  | |_| | |_) |  __/ |  | |____| |____ _| |_ 
|_| |_|\__, | .__/ \___|_|   \_____|______|_____|
         __/ | |                                 
        |___/|_|                                 
""")

    print("Simple file automation utility")
    print("Type 'help' to see commands.\n")

def main():
    print_banner()
    processor = CommandProcessor()
    
    while True:
        try:
            user_input = input("HyperCLI > ")
            result = processor.process(user_input)
            
            if result == "exit":
                print("Shutting down HyperCLI. Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\nForced shutdown. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
