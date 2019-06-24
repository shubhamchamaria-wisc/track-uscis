import requests
import asyncio
import aiohttp

processed = 0
processing = 0
other = 0
ret_list = []
apiUrl = 'https://egov.uscis.gov/casestatus/mycasestatus.do'

def separate(s):
	char = s.rstrip('0123456789')
	num = s[len(char):]
	return char, num

def decide_outcome(status):
	global processed
	global processing
	global other
	if "Card " in status:
		processed += 1
	elif status == "Case Was Received" or status == "Fees Were Waived":
		processing += 1
	else:
		other += 1

def check_ban(caseId):
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	response = requests.post(apiUrl, data = {'appReceiptNum': caseId}, headers=headers)
	if(response.status_code == requests.codes.ok and str(response.content).find("IP address or internet gateway has been locked out") != -1):
		return True
	else:
		return False

def check_validity(caseId):
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	response = requests.post(apiUrl, data = {'appReceiptNum': caseId}, headers=headers)
	if(response.status_code == requests.codes.ok and str(response.content).find("Validation Error(s)") == -1):
		return True
	else:
		return False

def process_tokens(caseId):
	caseId = separate(caseId)
	idList = []
	num_cases = 1000
	step_size = 10
	i = num_cases
	while i > 0:
		tmpCase = caseId[0] + str(int(caseId[1]) - i)
		idList.append(tmpCase)
		i -= step_size
	i = 0
	while i <= num_cases:
		tmpCase = caseId[0] + str(int(caseId[1]) + i)
		idList.append(tmpCase)
		i += step_size
	id_json = [{"appReceiptNum": c} for c in idList]
	return id_json

async def parallel_post(token_list):
	global ret_list
	status_list = []
	async with aiohttp.ClientSession() as session:
		for token in token_list:
			status = asyncio.ensure_future(post_case(token, session))
			status_list.append(status)
		response = await asyncio.gather(*status_list)
		for r,t in zip(response,token_list):
			r = str(r)
			case = r[r.find("<h1>")+4:r.find("</h1>")]
			ret_list.append([t['appReceiptNum'],case])
			decide_outcome(case)


async def post_case(token, session):
	header = {'Content-Type': 'application/x-www-form-urlencoded'}
	async with  session.post(apiUrl, data=token, headers=header) as response:
		return await response.read()

def main(caseId):
	global processed
	global processing
	global other
	global ret_list
	processed = 0
	processing = 0
	other = 0
	ret_list = []
	if(check_ban(caseId)):
		return 0,0,0,2, ret_list
	if(check_validity(caseId)):
		token_list = process_tokens(caseId)
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		future = asyncio.ensure_future(parallel_post(token_list))
		loop.run_until_complete(future)
		print(ret_list)
		return processed, processing, other, 1, ret_list
	else:
		return 0,0,0,0, ret_list
if __name__ == '__main__':
    main()
