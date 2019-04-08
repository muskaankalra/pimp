from powerball import PowerBall

class Homepage():
  def __init__(self):
    	self.status = 0 # the game's initial status is 0, 0 means the game is still on the homepage
  
  def input(self,string):
    #if self.status === 0, choose Service
    if self.status == 0:
      if string >="1" and string <= "6":
        self.response = self.choose_game(sring)
      else:
        self.response = "Improper input."
    elif self.status == 1:
      self.responese = self.powerball.input(string)
          #self.response = ClientPowerBall.response
    else:
      self.responese = "Error!!!"

    return self.response
        
  
  def welcome_narratives(self):
    response = "Welcome to the Golden Nugget Casino!"
    respone += "WHERE FRIENDSHIP IS THE LARGEST JACKPOT!\n\n"
    """
    response += "May we all be winners -> complete assignemnts, pass this course, get straight As, and an internship & job.\n"
    response += "Speaking of internships and jobs, we have an expert team here at Golden Nugget to assist with your career needs:\n"
    response += "-10 Bitpoints for resume review or cover letter review\n"
    response += "-100 bitpoints for writing your cover letter\n"
    response += "-250 bitpoints for internship/job referral\n\n"
    response += "Casino Services Menu:\n"
    response += "1. Powerball\n"
    """
    return response
      
      
  def choose_game(self, userInput):
    output = ""
    if userInput == "1":
        self.status = 1
        self.powerball = Powerball()
        output = self.powerball.start()
    elif userInput == "2":
        self.status = 2
    elif userInput == "3":
        self.status = 3
    elif userInput == "4":
        self.status = 4
    elif userInput == "5":
        self.status = 5
    elif userInput == "6":
        self.status = 6
    else:
        output  = "Please enter a single digit of your choice."
    return output
