import requests
import re
from argparse import ArgumentParser

cli_args = None


class PatternChecker:
    def __init__(self, pattern):
        self.target, self.pattern = pattern.split(":")

    def check(self, json_data):
        target = self.target.split(".")

        crr = json_data
        for key in target:
            if key not in crr:
                return False

            crr = crr[key]

        if type(crr) != str:
            return False

        return re.compile(self.pattern).match(crr) != None

    def __str__(self):
        return f"{self.target}:{self.pattern}"


def send_request():
    global cli_args

    headers = {}
    if cli_args.headers:
        for header in args.headers:
            k, v = header.split(":")
            headers[k] = v

    params = {}
    if cli_args.params:
        for param in args.params:
            k, v = param.split(":")
            params[k] = v

    return requests.request(cli_args.method, cli_args.url, params=params,
                            headers=headers, cookies=cli_args.cookies)


def check_pattern(res):
    global cli_args

    oks = []
    if cli_args.pattern:
        for pat in [PatternChecker(p) for p in cli_args.pattern]:
            success = pat.check(res.json())
            oks.append(success)

    return oks


def report_slack(results):
    global cli_args

    if not cli_args.slack:
        return
    
    success = all(results)
    
    if success and not cli_args.alert_success:
        return
    
    if not success and not cli_args.alert_failed:
        return

    message = {
        "text": f"API health check result",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Application: {cli_args.name}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"Pattern: {p} got result {'success' if s else 'failed'}"
                    } for p, s in zip(cli_args.pattern, results)
                ]
            }
        ]
    }

    response = requests.post(cli_args.slack,
                             headers={
                                "Content-type": "application/json"
                             },
                             json=message)


def report_result(results):
    global cli_args

    print(f"Checked {len(results)} patterns")
    ok, failed = 0, 0
    for success, pat in zip(results, cli_args.pattern):
        if cli_args.verbose:
            print(f"Pattern [{pat}] {'success' if success else 'failed'}")

        if success:
            ok += 1
        else:
            failed += 1

    print(f"Success: {ok}, Failed: {failed}")

    report_slack(results)


def main():
    parser = ArgumentParser()
    parser.add_argument("-u", "--url",
                        dest="url",
                        help="URL to request")
    parser.add_argument("-n", "--name",
                        help="Name of the api")
    parser.add_argument("-m", "--method",
                        dest="method",
                        help="HTTP method to use",
                        default="GET")
    parser.add_argument("-p", "--param",
                        dest="params",
                        help="Parameters to send",
                        action="append")
    parser.add_argument("-c", "--cookie",
                        dest="cookies",
                        help="Cookies to send",
                        default=None)
    parser.add_argument("-H", "--header",
                        dest="headers",
                        help="Headers to send",
                        action="append")
    parser.add_argument("-P", "--pattern",
                        dest="pattern",
                        help="Pattern to check api health",
                        action="append")
    parser.add_argument("-as", "--alert-success",
                        action="store_true",
                        default=False)
    parser.add_argument("-af", "--alert-failed",
                        action="store_true",
                        default=False)
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        default=False)
    parser.add_argument("--slack",
                        dest="slack",
                        help="Slack webhook url",
                        default=None)

    global cli_args
    cli_args = parser.parse_args()

    if not cli_args.url:
        print("URL cannot be empty")
        return

    if not cli_args.name:
        print("Name cannot be empty")
        return

    res = send_request()

    if res.status_code != 200:
        print(f"Request failed with status code {res.status_code}")
        return

    ok = check_pattern(res)
    report_result(ok)


if __name__ == "__main__":
    main()
