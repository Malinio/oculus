from pprint import pprint


def get_parsed_message(message):
    message = message.strip()
    message_elements = message.split(':')
    message = {
        'side': message_elements[0],
        'action': message_elements[1],
        'action_time': message_elements[2],
        'frame_num': message_elements[3],
    }
    return message


def get_parsed_log(filename):
    parsed_logs = []
    with open(filename) as logs_file:
        for record in logs_file.readlines():
            record_time, message = record.split(' ')
            message = get_parsed_message(message)
            parsed_logs.append({
                'record_time': record_time,
                'message': message
            })

    return parsed_logs


def main():
    oculus_logs = get_parsed_log('logs/screen_share_oculus.log')
    victima_logs = get_parsed_log('logs/screen_share_victima.log')

    all_logs = [*oculus_logs, *victima_logs]
    all_logs.sort(key=lambda log: log['record_time'])

    with open('logs/overall.log', 'w') as overall_log:
        for log in all_logs:
            overall_log.write(
                f'{log["record_time"]} - {log["message"]["side"]} - '
                f'{log["message"]["action"]}: {log["message"]["action_time"]} (frame_num: {log["message"]["frame_num"]})'
            )
            overall_log.write('\n')


if __name__ == '__main__':
    main()
