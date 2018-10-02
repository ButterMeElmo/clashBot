/*
	Inspired by Devsome
*/


const clashApi = require("clash-of-clans-api");
var request = require("request");
var fs = require("fs");
var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;

// Loading my Configs
var config = require("./config_bot.json");
// fs.writeFileSync( __dirname + '/config_bot.json' , JSON.stringify(config));

// choose which token here
let clashClient = clashApi({
	token:config.token_to_use
  });


//clashClient
  // .clanByTag(config.my_clan)
 //  .then(response => console.log(response))
//   .catch(err => console.log(err));

function getNameAndNumberFromID(response, tag, isEnemy) {
	
	var listToUse = response.clan.members;
	if (isEnemy) {
		listToUse = response.opponent.members;
	}
	for (index in listToUse) {
		var member = listToUse[index];
		
		if (member.tag == tag) {
			return member.mapPosition + " " + member.name;
		}
	}
}

function printWarLog(response) {
	for (index in response.items) {
		var entry = response.items[index];
		//console.log(entry);
		var clanBeingEvaluated = entry.clan
		var output = entry.result + " " + entry.teamSize + " man war"
		//console.log(output)
		output = "self: " + clanBeingEvaluated.stars + " stars, " + clanBeingEvaluated.destructionPercentage + "% destruction"
		//console.log(output)
		var clanBeingEvaluated = entry.opponent
		output = "enemy: " + clanBeingEvaluated.stars + " stars, " + clanBeingEvaluated.destructionPercentage + "% destruction"
		//console.log(output)
		//console.log("");
	}
}

function parseDate(date) {
	var year = date.slice(0,4)
	var month = parseInt(date.slice(4,6))-1
	var day = date.slice(6,8)
	var hour = date.slice(9,11)
	var min = date.slice(11,13)
	var sec = date.slice(13,15)
	return new Date(Date.UTC(year,month, day, hour, min, sec));
}

function getWarAsString(response, getOverview, getOurAttacks, getTheirAttacks){ 
	if (response.state == "notInWar") {
		return response.state;
	}
// 	console.log(response);
	var result = "";
	var us = response.clan;
	var enemy = response.opponent;
	result += us.name + " vs " + enemy.name + "\n\n";
	var prepStart = parseDate(response.preparationStartTime)
	var warStart = parseDate(response.startTime)
	var warEnd = parseDate(response.endTime)
	var dateNow = new Date();
	var timeRemaining =  warStart - dateNow;
	var warDay = "Prep Day";
	if (response.state == "inWar") {
		warDay = "War Day";
		timeRemaining = warEnd - dateNow;
	}
	else if (response.state == "warEnded") {
		warDay = "War Over";
		timeRemaining = 0;
	}

	timeRemaining = timeRemaining / 1000;
    var minutesRemaining = Math.floor(timeRemaining / 60);
	var secondsRemaining = timeRemaining % 60;
	var hoursRemaining = Math.floor(minutesRemaining / 60);
	minutesRemaining = minutesRemaining % 60;

	result += "Time remaining: "  + hoursRemaining + "h " + minutesRemaining + "m" + "\n"
	result += us.name + ":\n"
	result += us.stars + "/" + response.teamSize*3 + " stars\n"
	result += us.destructionPercentage + "% damage\n"
	result += us.attacks + "/" + response.teamSize*2 + " attacks used\n\n"
	result += enemy.name + ":\n"
	result += enemy.stars + "/" + response.teamSize*3 + " stars\n"
	result += enemy.destructionPercentage + "% damage\n"
	result += enemy.attacks + "/" + response.teamSize*2 + " attacks used\n\n"

	var isEnemy;
	if (getOurAttacks) {
		isEnemy = false;
		//result += getAllAttacksByClan(us, response, isEnemy)
	}
	
	if (getTheirAttacks) {
		isEnemy = true;
		result += getAllAttacksByClan(enemy, response, isEnemy)
	}
	
	
	return result
}

function getAllAttacksByClan(clan, response, isEnemy) {
	result = "";
	var map = new Map();
	for (index in clan.members) {
		var member = clan.members[index];
		var tempresult = getAllAttacksByMember(member, response, isEnemy)
		map.set(member.mapPosition, tempresult)
	}
	var i;
	for (i = 1; i <= response.teamSize; i++) { 
    	result += map.get(i);
	}
	return result;
}

function getAllAttacksByMember(member, response, isEnemy) {
	var result = "";
	result += member.mapPosition + ". " + member.name + "\n";
	var attack1 = "Unused";
	var attack2 = "Unused";
	if (member.attacks != undefined) {
		//console.log(member.attacks)
		if (member.attacks.length > 0) {
			var attack = member.attacks[0];
			attack1 = getNameAndNumberFromID(response, attack.defenderTag, !isEnemy) + " " +
			 attack.stars + " stars " + attack.destructionPercentage + "%";
		}	
		if (member.attacks.length > 1) {
			var attack = member.attacks[1];
			attack2 = getNameAndNumberFromID(response, attack.defenderTag, !isEnemy) + " " +
			attack.stars + " stars " + attack.destructionPercentage + "%";
		}
	}
	result += "Attacks:" + "\n";
	result += "1) " + attack1 + "\n";
	result += "2) " + attack2 + "\n\n";
	return result;
}

var my_clan = config.my_clan;
var other_clan = config.other_clan;
var currentClan = my_clan;


function getCurrentWarOverview() {
	var getOverview = true;
	var getOurAttacks = false;
	var getTheirAttacks = false;
	return	clashClient
   				.clanCurrentWarByTag(currentClan)
				.then(response => {
					getWarAsString(response, getOverview, getOurAttacks, getTheirAttacks);
					saveDataToFile(response, 'warDetailsLog')
				})
}

function getCurrentWarDetailed() {
	var getOverview = true;
	var getOurAttacks = true;
	var getTheirAttacks = true;
	return	clashClient
   				.clanCurrentWarByTag(currentClan)
				.then(response => getWarAsString(response, getOverview, getOurAttacks, getTheirAttacks))
}

function getAndSavePlayerAchievements(response) {
	var results = []
	var listToUse = response.memberList;
        for (index in listToUse) 
	{
                var member = listToUse[index];
		clashClient.playerByTag(member.tag).then(response => 
		{
			results.push(response); 
			if (results.length == listToUse.length)
			{
				resultsDict = {}
				resultsDict['members'] = results;
				saveDataToFile(resultsDict, 'clanPlayerAchievements');
			}
		}
		).catch(err => console.log(err));
        }
}

function getClanDetails() {
	return clashClient
  		.clanByTag(currentClan)
  		.then(response => { 
			//console.log(response); 
			getAndSavePlayerAchievements(response);  saveDataToFile(response, 'clanLog')})
  		.catch(err => console.log(err));
}

// seems to be a subset of getClanDetails
// function getClanMemberDetails() {
// 	return clashClient
//   		.clanMembersByTag(currentClan)
//   		.then(response => console.log(response))
//   		.catch(err => console.log(err));
// }



function getWarLog() {
	return clashClient
	  .clanWarlogByTag(currentClan)
	  .then(response => {printWarLog(response); saveDataToFile(response, 'warLog')})
	  .catch(err => console.log(err));
}


function saveDataToFile(dataToSave, fileName) {
	var now = new Date();
	fileName = fileName + "_" + now.getUTCFullYear() + "-"+ (now.getUTCMonth() + 1) + "-" + now.getUTCDate() +'.json';
	var filePath = "data/" + fileName;
	var fs = require("fs");
	var jsonContent = [];
	if (fs.existsSync(filePath)) {
		var contents = fs.readFileSync(filePath);
	 	jsonContent = JSON.parse(contents);
	}
 	dataToSave['timestamp'] = + new Date();
 	jsonContent.push(dataToSave);
 	fs.writeFileSync(filePath, JSON.stringify(jsonContent, null, 4))
}




module.exports.getCurrentWarOverview = getCurrentWarOverview
module.exports.getCurrentWarDetailed = getCurrentWarDetailed

//getCurrentWarOverview();

getWarLog();
getClanDetails();
getCurrentWarOverview();

// client
//   .clanByTag(other_clan)
//   .then(response => console.log(response))
//   .catch(err => console.log(err));

// client
//   .clanMembersByTag(other_clan)
//   .then(response => console.log(response))
//   .catch(err => console.log(err));

// clashClient
//   .clanWarlogByTag(other_clan)
//   .then(response => printWarLog(response))
//   .catch(err => console.log(err));

// clashClient
//    .clanCurrentWarByTag(other_clan)
//    .then(response => console.log(getWarAsString(response)))
//    .catch(err => console.log(err));

