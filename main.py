"""
A dead-simple, in-terminal, spaced-repetition software
to be used as a locally hosted study resource
"""

VERSION = 1.0

#===== Imports =====#

try:
  import sys
  import os
  import random
  import datetime
  import sqlite3
  import uuid
except ImportError as e:
  print(f"Error loading module: {e}")
  sys.exit(2)

#===== sys functions =====#

def exit_program():
  print("\nGoodbye")
  sys.exit(0)

#===== scheduling struct =====#

schedule_dict = {
  1: {
    "interval": 0,
    "next": 1
  }, 2: {
    "interval": 2,
    "next": 1
  }, 3: {
    "interval": 4,
    "next": 1
  }, 4: {
    "interval": 8,
    "next": 1,
  }, 5: {
    "interval": 16,
    "next": 1
  }, 6: {
    "interval": 32,
    "next": 1
  }, 7: {
    "interval": 64,
    "next": 0
  }
}

#===== db connection =====#

conn = sqlite3.connect('db.db')
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

#===== db functions =====#

def add_card(front, back, deck_id):
  today = datetime.datetime.now().isoformat()
  cursor.execute("INSERT INTO cards (front, back, review_date, deck_id) VALUES (?, ?, ?, ?) ", (front, back, today, deck_id))
  conn.commit()

def advance_level(front, back):
  cursor.execute("SELECT level FROM cards WHERE front = ? AND back = ?;", (front, back))
  current_level = cursor.fetchone()[0]
  new_level = current_level + schedule_dict[current_level]["next"]
  new_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=schedule_dict[new_level]["interval"])
  cursor.execute("UPDATE cards SET level = ?, review_date = ? WHERE front = ? AND back = ?;", (new_level, new_date, front, back))
  conn.commit()

def regress_level(front, back):
  cursor.execute("UPDATE cards SET level = 1 WHERE front = ? AND back = ?;", (front, back))
  conn.commit()

def get_todays_cards(deck_id):
  today = datetime.date.today()
  tomorrow = datetime.date.today() + datetime.timedelta(days=1)
  cursor.execute("SELECT * FROM cards WHERE cards.deck_id = ? AND review_date BETWEEN ? and ?;", (deck_id, today, tomorrow))
  cards = cursor.fetchall()
  return cards

def get_missed_cards(deck_id):
  cursor.execute("SELECT * FROM cards WHERE cards.deck_id = ? AND review_date < date('now');", (deck_id,))
  cards = cursor.fetchall()
  return cards

def get_decks():
  cursor.execute("SELECT * FROM decks;")
  decks = cursor.fetchall()
  return decks

def get_deck_id_from_name(name):
  cursor.execute("SELECT * FROM decks WHERE name = ?;", (name,))
  deck = cursor.fetchone()
  return deck[0]

def add_deck(name):
  deck_id = str(uuid.uuid4())
  cursor.execute("INSERT INTO decks (deck_id, name) VALUES (?, ?);", (deck_id, name))
  conn.commit()

def delete_deck(name):
  cursor.execute("SELECT deck_id FROM decks WHERE name = ?;", (name,))
  deck_id = cursor.fetchone()[0]
  cursor.execute("DELETE FROM cards WHERE deck_id = ?;", (deck_id,))
  cursor.execute("DELETE FROM decks WHERE deck_id = ?;", (deck_id,))
  conn.commit()

#===== user selection functions =====#

def back_to_main_menu():
  input("Type [ENTER] to continue...")
  display_instructions()

def display_instructions():
  os.system('clear')
  print(
"""
Welcome to MOOG-MEMBERS
Please select from the following options:
 - [CREATE] a new deck
 - [STUDY] an existing deck
 - [ADD] a card to an existing deck
 - [DELETE] a deck
 - or type "help" to see an introduction
"""
)

def display_help_message():
  print(
"""
MOOG-MEMBERS is an offline and in-terminal spaced-repetition system (SRS)
All cards are given a level of 1-7 for how well-known it is. Every card
starts out at level 1, and each time you successfully recall a word, it
is moved up one level. If you fail to recall a word at any level, however,
it is placed back in level one. You can think of this program as a digital
Leitner Box. 

The spaced-repetition algorithm is very simple. Each time you recall a 
card that you view, the delay will increase by the next power of two. For
example, level 1 cards are reviewed every day, level 2 cards every 2 days,
level 3 cards every 4 days, level 4 every 8 and so on.  The max level for
a card is 7, meaning the maximum interval for review is 64 days. 

You're incentivised to study every day. If you miss a day of studying for 
which reviews were scheduled, these cards won't lose their level. They will
simply be reviewed on the day you return to studying. However, keeping to 
the schedule as best you can may yield better results.

It may come about that there are no cards to review on a given day. This 
is normal. 

If you would like to exit the program, type CTRL+C or type any of the
following words:
 - QUIT
 - EXIT
 - CLOSE
 - TERMINATE
 - GOODBYE
 - BYE

If you have any problems or would like to suggest a fix, send me an email 
at mookielagaras@gmail.com
"""
  )
  back_to_main_menu()

def create_deck():
  while True:
    deck_name = input("Deck name: ").strip()
    if deck_name == '':
      print("Name cannot be empty")
    else:
      add_deck(deck_name)
      print(f"New deck {deck_name} successfully added")
    break
    back_to_main_menu()

def select_deck_to_delete():
  os.system("clear")
  decks = get_decks() 
  if len(decks) < 1:
    print("No decks to delete")
    return
  else:
    os.system('clear')
    print("Available Decks:")
    for deck in decks:
      print(" -", deck[1])
    while True:
      deck_name = input("Select a deck to delete: ")
      if deck_name not in [deck[1] for deck in decks]:
        print(f"Deck {deck_name} does not exist")
      else:
        delete_deck(deck_name)
        os.system("clear")
        print(f"Deck {deck_name} successfully deleted")
        back_to_main_menu()
      break

def get_cards_from_deck():
  os.system("clear")
  decks = get_decks()
  print("Available Decks:")
  for deck in decks:
    print(" -", deck[1])
  while True:
    deck = input("Select a deck to study: ")
    if deck not in [deck[1] for deck in decks]:
      print(f"Deck {deck} does not exist")
      return
    else: 
      deck_id = get_deck_id_from_name(deck)
      cards = get_todays_cards(deck_id)
      return cards, deck_id

def study_cards():
  try:
    os.system("clear")
    cards, deck_id = get_cards_from_deck()
    cards += get_missed_cards(deck_id)
    if len(cards) < 1:
      os.system("clear")
      print("Can't study an empty deck... Try adding cards first!")
      back_to_main_menu()
      return
    while len(cards) > 0:
      cards = get_todays_cards(deck_id) + get_missed_cards(deck_id)
      card = random.shuffle(cards)
      for card in cards:
        print("Front:", card[0])
        input()
        print("Back:", card[1])
        known = input("Press ENTER if you knew it and anything else if you didn't: ")
        if known != "":
          regress_level(card[0], card[1])
        else:
          advance_level(card[0], card[1])
        os.system("clear")
    print("That's all the cards for today")
    back_to_main_menu()
  except TypeError as e:
    print(f"Something went wrong... maybe the deck was empty?\nTry adding cards to your deck: {e}")
    back_to_main_menu()

def add_cards():
  os.system("clear")
  decks = get_decks()
  print("Available Decks:")
  while True:
    for deck in decks:
      print(" -", deck[1])
    deck = input("Select a deck to add to: ")
    if deck not in [deck[1] for deck in decks]:
      print(f"Deck {deck} does not exist")
      return
    else: 
      deck_id = str(get_deck_id_from_name(deck))
      print("You'll be continually prompted to enter fronts and backs of cards.")
      print("Type 'exit' on the front and back of a card to exit")
      while True:
        front = input("Front: ")
        back = input("Back: ")
        if front.strip().lower() == 'exit' and back.strip().lower() == 'exit':
          back_to_main_menu()
          return
        elif front.lower() == '' or back.lower() == '':
          print("No empty cards!")
        else:
          add_card(front, back, deck_id)
          os.system('clear')
          print("Successfully added card!")

#===== main =====#

def main():
  display_instructions()
  while True:
    quitting_words = ["quit", "exit", "close", "terminate", "goodbye", "bye"]
    options = ["add", "create", "study", "help", "delete"]
    selection = input()
    if selection == 'study':
      study_cards()
    if selection == 'create':
      create_deck()
    if selection == 'add':
      add_cards()
    if selection == 'delete':
      select_deck_to_delete()
    if selection == 'help':
      display_help_message()
    if selection in quitting_words:
      exit_program()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    exit_program()
