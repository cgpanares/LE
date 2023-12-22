import os

def createTemplate(temp_list_statement, created_script, prefix, outputloc, hostname, ssm_comment):
		print("Chosen Option: Create Template", flush=True)
		final_output = (outputloc if outputloc != "" else "")
		name_of_script = created_script.split("\\")
		final_name_script = (prefix + "-" if prefix != "" else "") + name_of_script[-1]
		output_used = (final_output + "\\" if final_output != "" else "") + final_name_script

		print("Filename: " + final_name_script, flush=True)
		print("Destination of the file: " + output_used, flush=True)

		with open(output_used, "w") as w:
				w.write(ssm_comment + "\n\n" if bool(ssm_comment) else "")
				w.write("""get-job|remove-job -Force\nfunction getRunningJobs{ return (get-job|select-object State|select-string -AllMatches "Running").Matches.Count }\n$a={\n""")
				script_file = open(created_script, encoding="utf-8-sig")
				read_file = script_file.readlines()
				w.write("".join(read_file))
				w.write("\n}\n")
				w.write("""\n$scriptname=$MyInvocation.MyCommand.name\n$filename="$scriptname-$(Get-Date -Format "yyyyMMdd-HHmmss").csv"\n#$filename="$scriptname-$(Get-Date -Format "yyyyMMdd").csv"
					""")
				w.write('\n$outfile="C:\\Users\\${env:UserName}\\Documents\\ExecuteSSMReport\\$filename"')
				w.write(( "\n$hostname=" + ','.join("'" + str(x) + "'" for x in hostname) if bool(hostname) else "\n"))
				w.write("\n\n$a=$a.ToString()\n\n\n")

				for line in temp_list_statement:
					w.write(line + "}\n")

				w.write("""\n\n\nwhile((getRunningJobs) -gt 0){\nget-job | format-table -Property ID, Name, State,PSBeginTime,PSEndTime -autosize\nwrite-host "Refreshing in 10 seconds"\nStart-Sleep -s 10\n}\n""")
				w.write("""Write-Host "All completed for $scriptname. Execution time:"\nGet-Job| foreach-object{\n$totaltime = "$($_.PSEndTime - $_.PSBeginTime)"\nWrite-Host\nWrite-Host "Job Name -> $($_.Name): $totaltime"\nReceive-Job $_.Name\n}""")
				script_file.close()

		return output_used