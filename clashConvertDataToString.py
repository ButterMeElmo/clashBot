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

def convert_war_attacks_to_string(wars_info):
	resultString = ""
	for war in wars_info['wars_participated_in']:
		war_details = war['war_details']
		war_day_start = war_details['war_day_start']
		war_day_end = war_details['war_day_end']
		war_id = war_details['war_id']
		war_result = war_details['result']
		for war_attack in war['war_attacks']:
			member_name = war_attack['member_name']
			attack_number = war_attack['attack_number']
			attacker_position = war_attack['attacker_position']
			defender_position = war_attack['defender_position']
			stars = war_attack['stars']
			destruction_percentage = war_attack['destruction_percentage']
			attacker_town_hall = war_attack['attacker_town_hall']
			defender_town_hall = war_attack['defender_town_hall']
		resultString += "\n"
	temp_result = str(wars_info) 
	return temp_result[0:min(200,len(temp_result))]
