# Explanation of Table

## Entries

One column is devoted to each metric, 3 rows to each puzzle.  The rows correspond to the three different natural tiebreakers.
These tiebreakers are each of the other two metrics individually, and their product.
For example, for cycle optimized solutions, the shown solutions will be the lowest cost, lowest area, and lowest cost*area.
Some solutions will be the winner for more than one tiebreaker; redundant trios are omitted.
The score with the lowest product of other two metrics is noted by a star.

On 21 March 2018, I added a 4th column, devoted to the sum of cost, cycles and area. (Or for production puzzles, cost, cycles and instructions).

On 24 March 2018, /u/12345ieee helped tremendously with revamping the update bot. It now includes gifs when they are linked in the comment, and the puzzle name is a fake link containing the current pareto frontier (mouse over to see frontier scores).

## Looping vs nonlooping, waste chain vs clean, etc.

To me, a solution need only bring up the completion screen to count.
However, I am open to adding separate entries for some puzzles according to suggestions.

## How to add your solution

Post your score as a comment to [this post](https://www.reddit.com/r/opus_magnum/comments/7scj7i/official_record_submission_thread/).

Comments should have the puzzle name, any scores associated with the puzzle, and any gifs associated with the scores all on the same line.
Gifs are expected to be boxed links, use the format

    name : [scoreA](linkA), [scoreB](linkB),...
    name2: [score2A](link2A)
    ...etc.

if uncertain.  Links will be added automatically if posted by trusted users, if you want to be added as a trusted user join the discord and message me.

Scores may be triplets or quadruplets.  u/GltyBystndr made a script that scrapes your solution folder and generates quadruplets in the form

    <cost>/<cycles>/<area>/<instructions>

Triplets should be

    <cost>/<cycles>/<area>

for free space puzzles, and

    <cost>/<cycles>/<instructions>

for production puzzles.

## Attribution

At the moment I do not have plans to attribute scores to users.
A big reason for this is how late the leaderboards showed up - I cannot claim that only one person has a given score for most of the campaign, and won't really make an effort to track down the first.
That said, I can be talked into attributing certain scores as they come in, provided they beat the existing score on a sufficiently complex puzzle.
I just don't want this to be primarily a competitive leaderboard, but rather an informative one.
People shouldn't worry about sharing their solutions for fear someone else snipes a piece off the tiebreaker.


# Leaderboards
