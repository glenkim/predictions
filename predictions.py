import argparse
import csv
from types import SimpleNamespace


def parse_match(raw_match):
    words = raw_match.split(' ')
    match_teams, match_type = words[:-1], words[-1][1:-1]
    pivot = match_teams.index('Vs')
    team1, team2 = ' '.join(match_teams[:pivot]), ' '.join(match_teams[pivot+1:])
    return SimpleNamespace(raw_match=raw_match, team1=team1, team2=team2, match_type=match_type)


def load_matches_from_responses(responses):
    with open(responses) as f:
        reader = csv.reader(f)
        header = reader.__next__()
        raw_matches = header[2:]
        f.close()
    ret = []
    for raw_match in raw_matches:
        match = parse_match(raw_match)
        # print(f"Loaded match: team1={match.team1} team2={match.team2} match_type={match.match_type}")
        ret.append(match)
    return ret


def sanitize_outcome(team):
    return f"{team} Victory"


def get_valid_outcomes(match):
    if match.match_type == 'Bo2':
        return ['Tie', sanitize_outcome(match.team1), sanitize_outcome(match.team2)]
    else:
        return [sanitize_outcome(match.team1), sanitize_outcome(match.team2)]

def get_outcome(match):
    valid_outcomes = get_valid_outcomes(match)
    print(f"\n{match.team1} v. {match.team2} - {match.match_type}")
    while True:
        try:
            for key in range(len(valid_outcomes)):
                print(f'{key} - {valid_outcomes[key]}')
            result = int(input("Please enter the match result: "))
            if result < 0 or result >= len(valid_outcomes):
                raise ValueError
        except ValueError as e:
            pass
        else:
            match.outcome = valid_outcomes[result]
            break

def get_aliased_match(last_match, new_match):
    team1 = new_match.team1
    team2 = ' '.join(last_match.outcome.split(' ')[:-1])
    match_type = new_match.match_type
    raw_match = f"{team1} Vs {team2} ({match_type})"
    return SimpleNamespace(raw_match=raw_match, team1=team1, team2=team2, match_type=match_type)


def matches_func(args):
    matches = load_matches_from_responses(args.responses)
    ret = []
    print("\nResults\n-------")
    last_match = None
    for match in matches:
        if last_match and (match.team2 == last_match.team1 or match.team2 == last_match.team2):
            if ' '.join(last_match.outcome.split(' ')[:-1]) == match.team2:
                get_outcome(match)
            else:
                match.outcome = f"alias={get_aliased_match(last_match, match).raw_match}"
        else:
            get_outcome(match)
            last_match = match
        ret.append([match.raw_match, match.outcome])
    with open(args.matches, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['match', 'outcome'])
        writer.writerows(ret)
        f.close()


def load_matches(matches):
    with open(matches) as f:
        reader = csv.DictReader(f)
        ret = []
        while True:
            try:
                row = reader.__next__()
                obj = SimpleNamespace(match=row['match'], outcome=row['outcome'], predictions={})
                # print(f"Loaded match: match={obj.match} outcome={obj.outcome}")
                ret.append(obj)
            except StopIteration:
                break
        f.close()
    return ret


def load_responses(responses):
    with open(responses) as f:
        reader = csv.reader(f)
        header = reader.__next__()
        ret = []
        while True:
            try:
                row = reader.__next__()
                obj = SimpleNamespace(name=row[1], score=0, predictions={})
                for i in range(2, len(row)):
                    obj.predictions[header[i]] = row[i]
                # print(f"Loaded response: name={obj.name} predictions={obj.predictions}")
                ret.append(obj)
            except StopIteration:
                break
        f.close()
    return ret


def get_place(place):
    if place % 10 == 1:
        return f"{place}st"
    elif place % 10 == 2:
        return f"{place}nd"
    elif place %10 == 3:
        return f"{place}rd"
    else :
        return f"{place}th"


def scores_func(args):
    matches = {}
    aliases = {}
    for row in load_matches(args.matches):
        if row.outcome.find("alias=") < 0:
            for outcome in get_valid_outcomes(parse_match(row.match)):
                row.predictions[outcome] = []
            matches[row.match] = row
        else:
            aliases[row.match] = row.outcome.split('=')[1]
    for alias in aliases:
        matches[alias] = matches[aliases[alias]]
        matches[alias].predictions[sanitize_outcome(parse_match(alias).team2)] = []
    scores = []
    for row in load_responses(args.responses):
        row.correct = []
        row.incorrect = []
        for match in row.predictions:
            prediction = row.predictions[match]
            if prediction == matches[match].outcome:
                row.score = row.score + 1
                row.correct.append(SimpleNamespace(match=match, prediction=prediction))
            elif prediction:
                row.incorrect.append(SimpleNamespace(match=match, prediction=prediction))
            if prediction:
                matches[match].predictions[prediction].append(row.name)
        needs_report = args.individual and row.name in args.individual
        if needs_report:
            print(f"Individual breakdown: {row.name}",
                  f"----------------------{'-'*len(row.name)}",
                  "",
                  f"Correct guesses ({len(row.correct)}):",
                  '\n'.join([f"{guess.match} - {guess.prediction}" for guess in row.correct]),
                  "",
                  f"Incorrect guesses ({len(row.incorrect)}):",
                  '\n'.join([f"{guess.match} - {guess.prediction}" for guess in row.incorrect]),
                  "",
                  sep="\n")
        scores.append(row)
    sorted_scores = sorted(scores, reverse=True, key=lambda x: x.score)
    print("Match breakdowns")
    print("----------------")
    for key in matches:
        if key in aliases:
            continue
        match = matches[key]
        print(f"{match.match}: {match.outcome} - {len(match.predictions[match.outcome])} correct guesses")
        for outcome, predictions in match.predictions.items():
            print(f"{outcome} ({len(predictions)}): {', '.join(predictions)}")
        print('')
    print("Today's Rankings")
    print("----------------")
    one_pointers = {}
    zero_pointers = []
    bucketed_scores = {}
    for score in sorted_scores:
        if score.score not in bucketed_scores:
            bucketed_scores[score.score] = []
        bucketed_scores[score.score].append(score.name)
        if score.score == 1:
            team = score.correct[0].prediction
            if team not in one_pointers:
                one_pointers[team] = []
            one_pointers[team].append(score.name)
        elif score.score == 0:
            zero_pointers.append(score.name)
    place = 1
    for score in bucketed_scores:
        print(f"{get_place(place)}: {' / '.join(map(lambda x: f'@'+x, bucketed_scores[score]))} ({score}pts)")
        place = place + len(bucketed_scores[score])
    print("")
    for team in one_pointers:
        print(f"{team} saved them from a Forsaken Oracle??? Award: {', '.join(map(lambda x: f'@'+x, one_pointers[team]))}")
    if zero_pointers:
        print(f"Forsaken Oracle??? award: {', '.join(map(lambda x: f'@'+x, zero_pointers))}")
    with open(args.scores, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'score'])
        writer.writerows(map(lambda score: [score.name, score.score], sorted_scores))
        f.close()



def load_scores(scores):
    with open(scores) as f:
        reader = csv.DictReader(f)
        ret = []
        while True:
            try:
                row = reader.__next__()
                obj = SimpleNamespace(name=row['name'], score=row['score'])
                # print(f"Loaded match: match={obj.match} outcome={obj.outcome}")
                ret.append(obj)
            except StopIteration:
                break
        f.close()
    return ret


def totals_func(args):
    unsorted_totals = []
    totals = {}
    day_number = 1
    for scores in args.scores:
        for row in load_scores(scores):
            if row.name not in totals:
                total = SimpleNamespace(name=row.name, scores={}, total_score=0)
                unsorted_totals.append(total)
                totals[total.name] = total
            totals[row.name].scores[day_number] = int(row.score)
            totals[row.name].total_score = totals[row.name].total_score + int(row.score)
        day_number = day_number + 1
    sorted_totals = sorted(unsorted_totals, reverse=True, key=lambda x: x.total_score)
    print("All Rankings")
    print("----------------")
    bucketed_totals = {}
    for total in sorted_totals:
        if total.total_score not in bucketed_totals:
            bucketed_totals[total.total_score] = []
        bucketed_totals[total.total_score].append(total.name)
    place = 1
    for total in bucketed_totals:
        print(f"{get_place(place)}: {' / '.join(map(lambda x: f'@'+x, bucketed_totals[total]))} ({total}pts)")
        place = place + len(bucketed_totals[total])
    with open(args.totals, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'total'] + [f"day {x} score" for x in range(1, day_number)])
        for total in sorted_totals:
            writer.writerow([total.name, total.total_score] +
                [total.scores[x] if x in total.scores else 0 for x in range(1, day_number)])
        f.close()
    

cmd = argparse.ArgumentParser(description='Predictions utilities')
subparsers = cmd.add_subparsers(title='subcommands',
                                    description='valid subcommands',
                                    help='additional help')

matches_cmd = subparsers.add_parser('matches', description='Generates a day matches file from user input')
matches_cmd.add_argument('--responses',
                         required=True,
                         nargs='?',
                         help='Predictions responses file')
matches_cmd.add_argument('--matches',
                         required=True,
                         nargs='?',
                         help='Match results file')
matches_cmd.set_defaults(func=matches_func)

scores_cmd = subparsers.add_parser('scores', description='Generates a day scores file from files')
scores_cmd.add_argument('--responses',
                         required=True,
                         nargs='?',
                         help='Predictions responses file')
scores_cmd.add_argument('--matches',
                         required=True,
                         nargs='?',
                         help='Match results file')
scores_cmd.add_argument('--scores',
                         required=True,
                         nargs='?',
                         help='Day scores file')
scores_cmd.add_argument('--individual',
                         nargs='+',
                         help='Report breakdowns for individuals')
scores_cmd.set_defaults(func=scores_func)

totals_cmd = subparsers.add_parser('totals', description='Generates score totals file from day score files')
totals_cmd.add_argument('--scores',
                         required=True,
                         nargs='+',
                         help='Day scores files')
totals_cmd.add_argument('--totals',
                         required=True,
                         nargs='?',
                         help='Score totals file')
totals_cmd.set_defaults(func=totals_func)

args = cmd.parse_args()
args.func(args)
