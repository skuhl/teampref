This program assists in assigning people onto teams based on their preferences.

A person's preferences are input as a "people.csv" file. Each person is on a row. Each row contains the following information:

 * Name of the person.

 * Current team. If the person is already assigned to a team (and should not be moved), the current team may be specified.

 * Team preferences. A comma delimited list of the team names that the person prefers to be a member of (first team listed is given the most priority). When you collect this information, you likely want to cap the number of preferred teams people may request.

 * Friends. A somma delimited list friends which you wish to be on the same team as. When you collect this information, you likely want to cap the number of friends people may list.

 * Foes. A somma delimited list of people the person wants to avoid. When you collect this information, you likely want to cap the number of friends people may list.

 * Traits. A comma delimited list of trait names. For example, every team might need a leader. A person could identify themselves as having the "Leader" trait.


The person who runs the program must also specify the following information in a "teams.csv" file. The software will not work unless this information is provided (and there is enough capacity in the teams for people to be assigned to them). Each row of this file contains the following information:

 * Team name

 * Maximum capacity of the team

 * The traits which we want to fill on the team. For example, we may wish that a team has 1 leader and 2 artists. A person can fulfill multiple roles. For example, if an individual answered that they can serve as a leader and as a artist, then a single person can satisfy two traits.



## Measuring Pain

When everybody is assigned to a team, we can calculate the "pain" of each person on the team. Pain is the sum of the following pieces of information:

* Team preferences (i.e., a list of teams which the person wants to be on), then being on the last team on the list will reduce the pain by 1. Being on the second to last team will reduce pain by 2, etc. If no team preferences are listed, then it plays no role in calculating pain.

* Friends. If Jane is on a team with one of her friends, then her pain is reduced by 1. If she is on a team with N of her friends, her pain is reduced by N.

* Foes. If Jane is on a team with one of foes, her pain is increased by 10.

* Unfilled traits: If a team has an unfilled trait (i.e., the team is supposed to have a leader but nobody has indicated that they can fill that role) the pain of every person on the team is increased by 3.

In summary: Any foes listed by people are taken seriously. Depending on the number of team preferences that the user lists, the team preferences may (or may) not have a string influence. Having traits fulfilled is moderately important. Specifying friends has a minimal impact. 

It may be useful to think of these values relative to each other:

 * It takes 10 friends on your team to offset the pain introduced by a foe.

 * If you can specify 3 team preferences, being on your top-ranked team has the same pain as being on a non-ranked team with 3 friends.

 * 3 unfilled traits is approximately the same amount of pain as being on a team with a foe


## Minimizing Pain

Once we have arranged everybody onto teams, we can measure the pain. First, we find the person (or people) experiencing the largest amount of pain. If there are 3 people experiencing a pain of 10 (and nobody with higher pain), we represent this solution as having a overall pain of "10.003" (integer part is the largest pain; next two digits are the number of people experiencing that pain). If we find a solution that would result in 10.002 (max pain 10, 2 people experiencing it), then that would be the new preferred solution. Similarly, if the software found a solution of 9.035 (max pain of 9, 35 people experiencing it), that would become the new, preferred solution. 

To find an arrangement that has minimal pain, we generate one possible solution, and then "mutate" or modify that solution repeatedly until we find a better solution. We perform this process on multiple processes. The software reports the best pain found for each processor as different "strains". Periodically, it will print an array representing the best pain found so far for each strain. When the user presses Ctrl+C, the best arrangement is printed to the console. In addition, an output.csv file output which is in the same format as the people.csv file.


## Running the program

When you run the program (python3 ./teampref.py), it expects teams.csv and people.csv to be present. We recommend that you run the program at least until it stops reporting that it has found a new best strain. You may let the program run for many minutes, hours or overnight. The solution that the program finds is not guaranteed to be optimal---only the best that the computer has found so far after randomly trying different permutations.

If you are not satisfied with the solution the program finds, you may wish to run the program multiple times and modify the input files (teams.csv and people.csv) to encourage it to make the choices which you prefer.

