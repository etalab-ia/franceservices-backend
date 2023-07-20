from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    from commands import execute_commands, COMMANDS_PARSER

    commands = vars(COMMANDS_PARSER.parse_args())
    execute_commands(**commands)
