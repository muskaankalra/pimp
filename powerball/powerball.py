import random

class PowerBall:
	def __init__(self, pool, lottery):
		self.id = ""
		self.pool = pool
		self.lottery = lottery
		self.quit = False
		self.status = 0  # 0 means just enter into the homepage 
		self.num = 0  # num is the Number of tickets client want to buy

	def getquit(self):
		return self.quit

	def GenerateRandom(self, num):
		randlist = []
		for i in range(0, num):
			randlist.append(random.randint(0,69))
		print(randlist)
		return randlist

	def input(self,choice):

		#string = "\nSelect from the following options:\n1. Pick your numbers\n2. Game Rules\n3. Claim your prize!\n4. Return to Homepage\n"
		response = ""

		if self.status == 0:
			if choice == "1":
				self.status = 1
				response = "Number of tickets you want to buy: "
		
			elif choice == "2":
				response = "EACH GAME IS WORTH 10 BITPOINTS\n1. Select five numbers from 1 to 69 or you can also choose a 'Randomly Generated Ticket' that gives you 5 randonly generated numbers\n2. Every Monday and Thursday the PowerBall rolls and 5 random winning numbers are displayed on our home page\n3. If 3 or more of your ticket numbers match with the winning numbers on the PowerBall, you win according to the Prizes listed\n4. To claim your prize, go to our home page and choose the 'Claim Prize' option"
				response = response + "\n\nSelect from the following options:\n1. Pick your numbers\n2. Game Rules\n3. Claim your prize!\n4. Return to Homepage\n"

			elif choice == "3":
				self.status = 3
				response = "Enter your numbers seperated by a comma: "

			elif choice == "4":
				self.quit = True
			else:
				response = "Improper input."
		elif self.status == 1:
			if choice.isdigit():
				self.num = int(choice)
				if self.num <= 0:
					response = "Improper input."
				else:
					response = "Do you want to choose your numbers? (Y)es or (N)o: "

			elif (choice == "Yes") or (choice == "Y") or (choice == "yes") or (choice == "y"): 
				if self.num <= 0:
					response = "Improper input."
				else:
					response = "Enter your numbers seperated by a comma: "

			elif ',' in choice:
				tickets = choice.split(",")
				tickets = [int(i) for i in tickets]
				response = "Your tickets are: {}".format(tickets)
			elif (choice == "No") or (choice == "N") or (choice == "no") or (choice == "n"):
				tickets = self.GenerateRandom(self.num)
				response = "Your tickets are: {}".format(tickets)
			else:
				response = "Improper input."

		elif self.status == 3:

			print("choice:"+choice)
			arr = choice.split(",")
			arr = [int(i) for i in arr]
			prize = game.CalPrize(arr)
			if prize != "":
				response = "\nCongrats! You won {} BITPOINTS".format(prize)
			else:
				response = "\nSorry!, You didnt win anything"
		else:
			response = "Error status!!!"


		print("ben:\n"+response)
		return response

	def start(self):
		self.quit = False
		response = "WELCOME TO POWERBALL!!\n" + "\nSelect from the following options:\n1. Pick your numbers\n2. Game Rules\n3. Claim your prize!\n4. Return to Homepage\n"
		return response


	def CalPrize(self, num):
		count = 0
		for i in num:
			if i in self.lottery:
				count = count + 1

		if count == 3:
			prize = 0.2 * self.pool
			return prize

		elif count == 4:
			prize = 0.3 * self.pool
			return prize

		elif count == 5:
			prize = 0.5 * self.pool
			return prize			


def main():
	print("WELCOME TO POWERBALL!!")
	lottery = [12, 24 ,35, 55, 22]
	game = PowerBall(1000, lottery)
	quit = False

	while quit == False:
		choice = int(input("\nSelect from the following options:\n1. Pick your numbers\n2. Game Rules\n3. Claim your prize!\n4. Return to Homepage\n"))
		if choice == 1:
			num = int(input("Number of tickets you want to buy: "))
			s = input("Do you want to choose your numbers? (Y)es or (N)o: ")
			if (s == "Yes") or (s == "Y") or (s == "yes") or (s == "y"):
				lottery = input("Enter your numbers seperated by a comma: ")
				tickets = lottery.split(",")
				tickets = [int(i) for i in tickets]

			else:
				tickets = game.GenerateRandom(num)

			print("Your tickets are: {}".format(tickets))
			
		elif choice == 2:
			print("EACH GAME IS WORTH 10 BITPOINTS\n1. Select five numbers from 1 to 69 or you can also choose a 'Randomly Generated Ticket' that gives you 5 randonly generated numbers\n2. Every Monday and Thursday the PowerBall rolls and 5 random winning numbers are displayed on our home page\n3. If 3 or more of your ticket numbers match with the winning numbers on the PowerBall, you win according to the Prizes listed\n4. To claim your prize, go to our home page and choose the 'Claim Prize' option")
			
		elif choice == 3:
			num = input("Enter your numbers seperated by a comma: ")
			arr = num.split(",")
			arr = [int(i) for i in arr]
			prize = game.CalPrize(arr)
			if prize != "":
				print("\nCongrats! You won {} BITPOINTS".format(prize))
			else:
				print("\nSorry!, You didnt win anything")

		elif choice == 4:
			quit = True
			


if __name__=="__main__":
	main()
