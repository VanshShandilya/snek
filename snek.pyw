# Python is bad with emojis so like yeah
# Please don't roast my code ;-;
# Adding tkinter
import os
import random
from collections import deque
import json
try:
    from mysql import connector
except ModuleNotFoundError:
    # Installing mysql python connector if not found.
    os.system('pip install mysql-connector-python')
    from mysql import connector
import tkinter as tk
from tkinter import ttk
import createdatabase
# creating the database if not present.
createdatabase.main()

class BodyNode:
    def __init__(self, x: int, y: int) -> None:
        self.symbol = '[]'
        self.x = x
        self.y = y
    
    def __repr__(self) -> str:
        return self.symbol

class Head(BodyNode):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.symbol = '()'
        self.direction = 'E' # Direction will be N(North/Up), S(South/Down), E(East/Right), W(West/Left).
    
    def move(self):
        # Move the head based on direction.
        if self.direction == 'N':
            self.y -= 1
        elif self.direction == 'S':
            self.y += 1
        elif self.direction == 'E':
            self.x += 1
        elif self.direction == 'W':
            self.x -= 1
    
    def checkmove(self) -> tuple:
        # Check where the head will be based on direction.
        if self.direction == 'N':
            return (self.x, self.y - 1)
        elif self.direction == 'S':
            return (self.x, self.y + 1)
        elif self.direction == 'E':
            return (self.x + 1, self.y)
        elif self.direction == 'W':
            return (self.x - 1, self.y)

class Fud:
    def __init__(self, gridx: int, gridy: int, black_list_coords: tuple) -> None:
        self.symbol = '<>'
        while True:
            # Get the random location that is not taken over by some other object.
            self.x = random.randrange(gridx)
            self.y = random.randrange(gridy)
            if (self.x, self.y) not in black_list_coords:
                break
    
    def __repr__(self) -> str:
        return self.symbol
    
    def replace(self, gridx: int, gridy: int, black_list_coords: tuple) -> None:
        while True:
            # same as __init__.
            self.x = random.randrange(gridx)
            self.y = random.randrange(gridy)
            if (self.x, self.y) not in black_list_coords:
                break

class Game(tk.Toplevel):
    def __init__(self, root: tk.Tk, icon: tk.PhotoImage, username: int, sizex: int=10, sizey: int=10, delay_ms: int=400, fud_count: int=2) -> None:
        super().__init__(root, background='black')
        # Initialising TopLevel.
        self.resizable(0, 0)
        self.title(f'Snek - {username}')
        self.iconphoto(False, icon)
        
        # Configuring style for widgets.
        self.__style = ttk.Style(self)
        self.__style.configure('Text.TLabel', font=('Arial', 15, 'bold'))
        self.__style.configure('Lost.Text.TLabel', font=('Arial', 15, 'bold'), foreground='#ff0000')
        self.__style.configure('Won.Text.TLabel', font=('Arial', 15, 'bold'), foreground='#00ff00')
        self.__style.configure('Grid.TLabel', font=('Courier New', 20, 'bold'))
        
        self.grass = '░░'
        self.sizex = sizex
        self.sizey = sizey
        # Head of the snake.
        self.__head = Head(x=1, y=self.sizey//2)
        # List for body of the snake.
        self.__snake = [BodyNode(x=0, y=self.sizey//2)]
        # Initialising all the fud on the map.
        self.__fud = [Fud(self.sizex, self.sizey, ((self.__head.x, self.__head.y),) + tuple(self.get_body_coords()))]
        
        for i in range(fud_count - 1):
            self.__fud.append(Fud(self.sizex, self.sizey, ((self.__head.x, self.__head.y),) + tuple(self.get_body_coords()) + tuple(self.get_fud_coords())))
        
        self.__controls_to_directions = {'W': 'N', 'S': 'S', 'D': 'E', 'A': 'W'}
        self.__black_list_directions = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        self.__move_queue = deque()
        self.__delay = delay_ms
        self.__username = username
        
        # Starting a SQL connection.
        with open('config.json', 'r') as f:
            self.cnx = connector.connect(**json.load(f)['SQL'])
        self.cnx.autocommit = True
        self.csr = self.cnx.cursor(dictionary=True)
        self.csr.execute('SELECT * FROM snekscores WHERE Username = %s', (username,))
        self.data = self.csr.fetchall()
        # Display highscore if user has one.
        if len(self.data) > 0:
            self.data = self.data[0]
            self.high_score_label = ttk.Label(self, text=f'Your High Score: {self.data["highScore"]}', style='Text.TLabel')
            self.high_score_label.grid(column=0, row=0)
        # Display the game grid.
        self.game_text = tk.StringVar(self)
        self.game_label = ttk.Label(self, textvariable=self.game_text, style='Grid.TLabel')
        self.game_close_button = ttk.Button(self, text='Close', width=35, command=self.destroy)
        
        self.game_label.grid(column=0, row=1)
        
        self.game_text.set(self.repr())
        
        # Keybinds for input.
        self.bind('<Key>', self.key_pressed)
        # Focusing on the screen.
        self.after(self.__delay, self.focus)
        # Starting the game loop.
        self.after(self.__delay, self.update)
        
        self.mainloop()
    
    def repr(self) -> str:
        self.represent = ''
        bodycoords = self.get_body_coords()
        fudcoords = self.get_fud_coords()
        for y in range(self.sizey):
            # Creating the grid.
            for x in range(self.sizex):
                if (x, y) in bodycoords:
                    self.represent += str(bodycoords[(x, y)])
                elif (x, y) == (self.__head.x, self.__head.y):
                    self.represent += str(self.__head)
                elif (x, y) in fudcoords:
                    self.represent += str(fudcoords[(x, y)])
                else:
                    self.represent += self.grass
            self.represent += '\n'
        return self.represent
    
    def key_pressed(self, event):
        # Keycodes - 87 - w, 65 - a, 83 - s, 68 - d
        if event.keycode in (87, 65, 83, 68):
            self.add_move(self.__controls_to_directions[event.keysym.upper()])
    
    def get_body_coords(self) -> dict:
        # Returns a dictionary with coordinates of body nodes as keys and the respective body nodes as values.
        coords = dict()
        for node in self.__snake:
            coords[(node.x, node.y)] = node
        return coords
    
    def get_fud_coords(self) -> dict:
        # Returns a dictionary with coordinates of fud as keys and the respective fud as values.
        coords = dict()
        for fud in self.__fud:
            coords[(fud.x, fud.y)] = fud
        return coords
    
    def move(self) -> None:
        # Updates the location of all body nodes to the location of the body node ahead of them.
        for i in range(len(self.__snake) - 1, 0, -1):
            self.__snake[i].x, self.__snake[i].y = self.__snake[i - 1].x, self.__snake[i - 1].y
        # Sets the location of the first body node to the location of the head.
        self.__snake[0].x, self.__snake[0].y = self.__head.x, self.__head.y
        # Updates the location of the head based on it's direction.
        self.__head.move()
    
    def add_move(self, direction: str) -> None:
        # Add Move in the move queue.
        if len(self.__move_queue) == 0:
            if direction != self.__black_list_directions[self.__head.direction]:
                self.__move_queue.append(direction)
        elif len(self.__move_queue) > 0 and len(self.__move_queue) < 3:
            if direction != self.__black_list_directions[self.__move_queue[-1]]:
                self.__move_queue.append(direction)
    
    def update(self) -> None:
        if len(self.__move_queue) > 0:
            # if move in movequeue, update the direction of head.
            self.__head.direction = self.__move_queue.popleft()
        
        # Gets the next location of the head.
        nextmove = self.__head.checkmove()
        
        #Gets the locations of all fud.
        fudcoords = self.get_fud_coords()
        
        # If next location of the head is in fud, add another node to body.
        if nextmove in fudcoords:
            fudcoords[nextmove].replace(self.sizex, self.sizey, ((self.__head.x, self.__head.y),) + tuple(self.get_body_coords()) + tuple(self.get_fud_coords()))
            tail = self.__snake[-1]
            self.__snake.append(BodyNode(tail.x, tail.y))
            # Stops the game if the grid fills up so that the replace method for fud does not end up in an infinite loop.
            if len(self.__snake) == self.sizex * self.sizey - 1 - len(self.__fud):
                self.move()
                self.high_score_label.grid_forget()
                self.won_label = ttk.Label(self, text=f'YOU WIN!\nScore: {len(self.__snake) - 1}', style='Won.Text.TLabel')
                self.won_label.grid(column=0, row=0)
                self.update_highscore()
                self.game_close_button.grid(column=0, row=2)
                return
        
        # Moves the snake by 1 frame.
        self.move()
        
        # Gets the location of all the body nodes.
        bodycoords = self.get_body_coords()
        
        # If the location of the snake head is colliding with a body part or snake is outside bounds, end game.
        if nextmove in bodycoords or nextmove[0] < 0 or nextmove[0] > self.sizex - 1 or nextmove[1] < 0 or nextmove[1] > self.sizey - 1:
            # If the user had a highscore then the label is forgotten, if they did not, have a highscore, nothing is done.
            try:
                self.high_score_label.grid_forget()
            except Exception as Err:
                if isinstance(Err, AttributeError):
                    pass
                else:
                    raise Err
            
            self.lost_label = ttk.Label(self, text=f'Game Over!\nScore: {len(self.__snake) - 1}', style='Lost.Text.TLabel')
            self.lost_label.grid(column=0, row=0)
            self.update_highscore()
            self.game_close_button.grid(column=0, row=2)
            return
        # If the game is not over, updates the display and schedules the next frame.
        else:
            self.game_text.set(self.repr())
            self.after(self.__delay, self.update)
        
    def update_highscore(self):
        # Get Score, 1 body node is provided by default.
        self.score = len(self.__snake) - 1
        # If user does not have a highscore, highscore is inserted.
        if len(self.data) == 0:
            self.csr.execute('INSERT INTO snekscores(Username, highScore) VALUES(%s, %s)', (self.__username, self.score))
        # If user has a highscore, and their current score is more than their highscore, highscore is updated.
        else:
            if self.score > self.data["highScore"]:
                self.csr.execute('UPDATE snekscores SET highScore = %s WHERE Username = %s', (self.score, self.__username))

def main():
    def play():
        # Disables the start button when no username is provided.
        def validate_username():
            if len(username_text.get()) > 0:
                username_submit_button.state(['!disabled'])
            else:
                username_submit_button.state(['disabled'])
        
        # Closes the TopLevel that asks for username and starts the game.
        def start_game():
            username_screen.destroy()
            game = Game(root, icon, username_text.get().capitalize())
        
        # Initialising TopLevel.
        username_screen = tk.Toplevel(root, background='black')
        username_screen.title('Snek - Play')
        username_screen.iconphoto(False, icon)

        # Setting up TopLevel.
        username_label = ttk.Label(username_screen, text='Username', style='Entry.TLabel')
        username_text = tk.StringVar(username_screen)
        username_text.trace('w', lambda *args: validate_username())
        username_entry = ttk.Entry(username_screen, textvariable=username_text)
        username_submit_button = ttk.Button(username_screen, text='Start', width=13, state='disabled', command=start_game)
        
        username_label.grid(column=0, row=0, sticky='sw')
        username_entry.grid(column=0, row=1)
        username_submit_button.grid(column=0, row=2)
        
        username_entry.focus()

    def leaderboard():
        # Initialising TopLevel.
        leaderboard_screen = tk.Toplevel(root, background='black')
        leaderboard_screen.title('Snek - Leaderboard')
        leaderboard_screen.iconphoto(False, icon)
        
        # Setting up TopLevel.
        leaderboard_heading_label = ttk.Label(leaderboard_screen, text='LEADERBOARD', style='Heading.TLabel')
        leaderboard_text = tk.StringVar(leaderboard_screen)
        leaderboard_label = ttk.Label(leaderboard_screen, textvariable=leaderboard_text)
        leaderboard_close_button = ttk.Button(leaderboard_screen, text='Close', width=23, command=leaderboard_screen.destroy)
        
        leaderboard_heading_label.grid(column=0, row=0)
        leaderboard_label.grid(column=0, row=1)
        leaderboard_close_button.grid(column=0, row=2)
        
        # Getting highscores of the top 10 players.
        csr.execute('SELECT * FROM snekscores ORDER BY highscore DESC LIMIT 10;')
        data = csr.fetchall()
        
        # If there are no highscores, display this msg.
        if len(data) == 0:
            leaderboard_text.set('No High Scores yet\nWill you be the first?\n')
        # If there are highscores, display them.
        else:
            for rank in range(len(data)):
                leaderboard_text.set(leaderboard_text.get() + f'{rank + 1}. {data[rank]["Username"]} - {data[rank]["highScore"]}\n')
        
        leaderboard_screen.mainloop()

    def rules():
        # Initialising TopLevel.
        rules_screen = tk.Toplevel(root, background='black')
        rules_screen.title('Snek - Rules')
        rules_screen.iconphoto(False, icon)
        
        # Setting up TopLevel.
        controls_heading_label = ttk.Label(rules_screen, text='CONTROLS', style='Heading.TLabel')
        controls_label = ttk.Label(rules_screen, text='W: Go Up\nD: Go Right\nS: Go Down\nA: Go Left')
        rules_heading_label = ttk.Label(rules_screen, text='RULES', style='Heading.TLabel')
        rules_label = ttk.Label(rules_screen, text='1. Running into walls -> Dead\n2. Running into yourself -> Dead\n3. Running into Food -> You get longer\nIf you fill up the screen, the game will end as that\'s the max possible length and points')
        rules_close_button = ttk.Button(rules_screen, text='Close', width=64, command=rules_screen.destroy)
        
        controls_heading_label.grid(column=0, row=0)
        controls_label.grid(column=0, row=1)
        rules_heading_label.grid(column=0, row=2)
        rules_label.grid(column=0, row=3)
        rules_close_button.grid(column=0, row=4)
        
        rules_screen.mainloop()
    
    # Initialising root window.
    root = tk.Tk()
    root.title('Snek')
    root.config(bg='black')
    root.resizable(0, 0)
    
    # Loading and setting up the snek icon.
    icon = tk.PhotoImage(file='Pictures\\snek.png')
    root.iconphoto(False, icon)
    
    # Configuring style for widgets.
    style = ttk.Style(root)
    style.theme_use('alt')
    style.configure('.', font=('Arial', 12), background='black', foreground='#dddddd')
    style.map('TButton', background=[('active', 'grey')])
    style.configure('TEntry', foreground='black')
    style.configure('Entry.TLabel', font=('Arial', 8, 'italic'), foreground='#aaaaaa')
    style.configure('Heading.TLabel', font=('Arial', 20, 'bold', 'underline'))
    
    # Setting up the Menu.
    text_label = ttk.Label(root, text='MENU', style='Heading.TLabel')
    play_button = ttk.Button(root, text='Play', width=20, command=play)
    leaderboard_button = ttk.Button(root, text='Leaderboard', width=20, command=leaderboard)
    rules_button = ttk.Button(root, text='Controls And Rules', width=20, command=rules)
    exit_button = ttk.Button(root, text='Exit', width=20, command=root.destroy)

    text_label.grid(column=0, row=0)
    play_button.grid(column=0, row=1)
    leaderboard_button.grid(column=0, row=2)
    rules_button.grid(column=0, row=3)
    exit_button.grid(column=0, row=4)
    
    root.mainloop()

# Running the main function
if __name__ == '__main__':
    with open('config.json', 'r') as f:
        cnx = connector.connect(**json.load(f)['SQL'])
    csr = cnx.cursor(dictionary=True)
    main()
    cnx.close()