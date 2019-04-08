from powerball import PowerBall

class Homepage():
  def __init__(self):
    	status = 0 # the game's initial status is 0, 0 means the game is still on the homepage
  
  def input(self,string):
    #if self.status === 0, choose Service
    if self.status == 0:
          if string >="1" and string <= "6":
            self.choose_game(sring)
          else:
            self.response = "Improper input."
    elif self.status == 1:
        	self.responese = self.powerball.input(string)
          #self.response = ClientPowerBall.response
    else:
        	self.responese = "Error!!!"

    return self.response
        
  
  def welcome_narratives(self):
      output = ""
      output += """
      Welcome to the Golden Nugget Casino!
  		WHERE FRIENDSHIP IS THE LARGEST JACKPOT!
      
      May we all be winners -> complete assignemnts, pass this course, get straight As, and an internship & job.
      
      Speaking of internships and jobs, we have an expert team here at Golden Nugget to assist with your career needs: 
      		-10 Bitpoints for resume review or cover letter review
          -100 bitpoints for writing your cover letter
          -250 bitpoints for internship/job referral
          
  		Casino Services Menu:
      		1. Powerball
          2. Roulette
          3. Deal or No Deal
          4. Career Assisstance # direct transfer with memo
          5. About Us
          6. Career with Golden Nugget Casino
          
  		Note: You can choose the menu by enter a single digit that is corresponding to the menu."
      """
      return output 
      
  def choose_game(self, userInput):
    output = ""
    if userInput == "1":
        self.status = 1
        self.powerball = Powerball()
        output = self.powerball.start()
    """
    elif userInput == "2":

        #call roulette
    elif userInput == "3":
        #call deal or no deal 
    elif userInput == "4":
        # career services
    elif userInput == "5":
      #call about us    
    elif userInput == "6":
      #call careers
    """
    else:
      output  = "Please enter a single digit of your choice."
    return output
