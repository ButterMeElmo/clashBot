def convert_donation_timeframe_results(results):
	if 'error' in results:
		return results['error']

	standard = results['standard']
	left_since_created = results['left_since_created']
	joined_since_created = results['joined_since_created']
	if len(standard) == 0 and len(left_since_created) == 0 and len(joined_since_created) == 0:
		return "No-one seems to have donated in that timeframe that fits these requirements"
	
	resultsString = ""
	if len(standard) > 0:
		resultsString += "These members donated the following amounts during this timeframe:\n"
		for entry in standard:
			resultsString += "{}: {}\n".format(entry["name"], entry["donated"])
	if len(joined_since_created) > 0:
		resultsString += "These members donated the following amounts during this timeframe (and are new members):\n"
		for entry in joined_since_created:
			resultsString += "{}: {}\n".format(entry["name"], entry["donated"])
	if len(left_since_created) > 0:
		resultsString += "These members left after the request was created so they may also have been responsible for filling it::\n"
		for entry in left_since_created:
			resultsString += "{}: {}\n".format(entry["name"], entry["donated"])
			
	return resultsString

def convert_war_attacks_to_string(war_attacks):
	return str(war_attacks)
