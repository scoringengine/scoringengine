#!/usr/bin/env ruby

require 'yaml'

num_of_teams = 23
$dapass = "Chiapet1"
$rootpass = "Chiapet1"
$domain = "nerdgov.net"
$basedn = "dc=nerdgov,dc=net"

def win_smb(team)
	check = {"name" => "WIN_SMB"}
	check["check_name"] = "SMBCheck"
	check["host"] = "192.168.#{team}.1"
	check["port"] = 445
	check["points"] = 100
	check["accounts"] = [
		{"username" => "administrator", "password" => $dapass},
	]
	check["environments"] = [{"matching_content" => "^SUCCESS"}]
	check["environments"][0]["properties"] = [
			{"name" => "remote_name", "value" => "DC"},
			{"name" => "share", "value" => "SHARE"},
			{"name" => "file", "value" => "flag.txt"},
			{"name" => "hash", "value" => "b10d4d79a2bbdd3b120a6d7fbcaea5f0d6708e56c10eef021d02052abfaa271b"},
		]
	return check
end

def nix_ssh(team)
	check = {"name" => "NIX_SSH"}
	check["check_name"] = "SSHCheck"
	check["host"] = "192.168.#{team}.2"
	check["port"] = 22
	check["points"] = 100
	check["accounts"] = [
		{"username" => "root", "password" => $rootpass}
	]
	check["environments"] = [{"matching_content" => "root"}]
	check["environments"][0]["properties"] = [
		{"name" => "commands", "value" => "cat /etc/shadow"},
	]
	check["environments"] << {"matching_content" => "PID"}
	check["environments"][1]["properties"] = [
		{"name" => "commands", "value" => "ps"},
	]
	return check
end

config = {}
config["teams"] = [
			{"name"  => "WhiteTeam","color" => "White","users" => [{"username" => "whiteteam", "password" =>"CHANGEME"}]},
			{"name"  => "RedTeam","color" => "Red","users" => [{"username" => "redteam", "password" =>"CHANGEME"}]},
		]

(1..num_of_teams).each do |x|
   config["teams"] << {"name"  => "team#{x}","color" => "Blue",
   		"users" => [{"username" => "team#{x}", "password" =>"CHANGEME"}],
   		"services" => [
   			win_smb(x), 
   			nix_ssh(x),
   		]
   	}
end

File.open("competition.yml", "w") { |file| file.write(config.to_yaml) }
