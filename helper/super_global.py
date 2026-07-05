import os


# Recursos del proyecto
PROJECT_PATH = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

IMAGE_PATH = os.path.join(
    PROJECT_PATH,
    "img"
)

LOGOS_PATH = os.path.join(
    IMAGE_PATH,
    "logos"
)

LOGO_COLEGIO_PATH = os.path.join(
    IMAGE_PATH,
    "logo_colegio.png"
)

LOGO_PETAPA_PATH = os.path.join(
    IMAGE_PATH,
    "logo_petapa.png"
)

MATEOLIMPIADAS_LOGO_PATH = os.path.join(
    LOGOS_PATH,
    "mateolimpiadas_logo.png"
)

MATEOLIMPIADAS_ICON_PATH = os.path.join(
    LOGOS_PATH,
    "mateolimpiadas_icon.png"
)

MATEOLIMPIADAS_ICO_PATH = os.path.join(
    LOGOS_PATH,
    "mateolimpiadas_icon.ico"
)

ICON_PATH = os.path.join(
    IMAGE_PATH,
    "icons"
)

ICON_SAVE_PATH = os.path.join(
    ICON_PATH,
    "save.png"
)

ICON_SEARCH_PATH = os.path.join(
    ICON_PATH,
    "search.png"
)

ICON_EDIT_PATH = os.path.join(
    ICON_PATH,
    "edit.png"
)

ICON_DELETE_PATH = os.path.join(
    ICON_PATH,
    "delete.png"
)

ICON_REFRESH_PATH = os.path.join(
    ICON_PATH,
    "refresh.png"
)

ICON_QUESTION_PATH = os.path.join(
    ICON_PATH,
    "question.png"
)

ICON_EXIT_PATH = os.path.join(
    ICON_PATH,
    "exit.png"
)

ICON_PLUS_PATH = os.path.join(
    ICON_PATH,
    "plus.png"
)

ICON_FOLDER_PATH = os.path.join(
    ICON_PATH,
    "folder.png"
)

ICON_IMAGE_PATH = os.path.join(
    ICON_PATH,
    "image.png"
)

ICON_GENERATE_CODE_PATH = os.path.join(
    ICON_PATH,
    "generate_code.png"
)

ICON_GENERATE_GAME_PATH = os.path.join(
    ICON_PATH,
    "generate_game.png"
)

ICON_OPEN_GAME_PATH = os.path.join(
    ICON_PATH,
    "open_game.png"
)

ICON_CHANGE_STATUS_PATH = os.path.join(
    ICON_PATH,
    "change_status.png"
)

ICON_SETTINGS_PATH = os.path.join(
    ICON_PATH,
    "settings.png"
)

ICON_CANCEL_PATH = os.path.join(
    ICON_PATH,
    "cancel.png"
)

ICON_START_PATH = os.path.join(
    ICON_PATH,
    "start.png"
)

ICON_PAUSE_PATH = os.path.join(
    ICON_PATH,
    "pause.png"
)

ICON_RESUME_PATH = os.path.join(
    ICON_PATH,
    "resume.png"
)

ICON_NEXT_PATH = os.path.join(
    ICON_PATH,
    "next.png"
)

ICON_FINISH_PATH = os.path.join(
    ICON_PATH,
    "finish.png"
)

ICON_GIVE_WORD_PATH = os.path.join(
    ICON_PATH,
    "give_word.png"
)

ICON_CORRECT_PATH = os.path.join(
    ICON_PATH,
    "correct.png"
)

ICON_INCORRECT_PATH = os.path.join(
    ICON_PATH,
    "incorrect.png"
)

ICON_REQUESTS_PATH = os.path.join(
    ICON_PATH,
    "requests.png"
)

ICON_STATISTICS_PATH = os.path.join(
    ICON_PATH,
    "statistics.png"
)

ICON_STOP_PATH = os.path.join(
    ICON_PATH,
    "stop.png"
)

ICON_FULLSCREEN_PATH = os.path.join(
    ICON_PATH,
    "fullscreen.png"
)

ICON_INFO_PATH = os.path.join(
    ICON_PATH,
    "info.png"
)

# __nombre de la base de datos incluyen el path
# La base de datos y las imágenes de cuestionarios son recursos externos.
# En un empaquetado futuro deben permanecer fuera del ejecutable.
PATH = r"C:\dataBaco\mateolimpiadas\\"
DATABASE_NAME = "olimpiadas.db"
FULL_PATH = PATH + DATABASE_NAME

# Estado de los cuestionarios
QUESTIONNAIRE_STATUS_DRAFT = "BORRADOR"
QUESTIONNAIRE_STATUS_ACTIVE = "ACTIVO"
QUESTIONNAIRE_STATUS_ARCHIVED = "ARCHIVADO"
QUESTIONNAIRE_STATUS = (
    QUESTIONNAIRE_STATUS_DRAFT,
    QUESTIONNAIRE_STATUS_ACTIVE,
    QUESTIONNAIRE_STATUS_ARCHIVED
)

# Áreas escolares
AREA_BASICOS = "Básicos"
AREA_DIVERSIFICADO = "Diversificado"
AREA_PRIMARIA = "Primaria"

AREAS = (
    AREA_PRIMARIA,
    AREA_BASICOS,
    AREA_DIVERSIFICADO
)

DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

# Reglas de negocio

MIN_QUESTIONS_PER_QUESTIONNAIRE = 5

MAX_QUESTION_TEXT_LENGTH = 500

MAX_ANSWER_TEXT_LENGTH = 250

# Estados de partidas
GAME_STATUS_DRAFT = "BORRADOR"
GAME_STATUS_WAITING = "ESPERANDO"
GAME_STATUS_IN_PROGRESS = "EN_CURSO"
GAME_STATUS_PAUSED = "PAUSADA"
GAME_STATUS_FINISHED = "FINALIZADA"
GAME_STATUS_CANCELLED = "CANCELADA"

GAME_STATUS = (
    GAME_STATUS_DRAFT,
    GAME_STATUS_WAITING,
    GAME_STATUS_IN_PROGRESS,
    GAME_STATUS_PAUSED,
    GAME_STATUS_FINISHED,
    GAME_STATUS_CANCELLED
)

RECOVERABLE_GAME_STATUS = (
    GAME_STATUS_WAITING,
    GAME_STATUS_IN_PROGRESS,
    GAME_STATUS_PAUSED
)

GAME_QUESTION_STATUS_PENDING = "PENDIENTE"
GAME_QUESTION_STATUS_CURRENT = "ACTUAL"
GAME_QUESTION_STATUS_ANSWERED = "CONTESTADA"
GAME_QUESTION_STATUS_NO_ANSWER = "SIN_RESPUESTA"
GAME_QUESTION_STATUS_CANCELLED = "ANULADA"

TEAM_STATUS_ACTIVE = "ACTIVO"
TEAM_STATUS_DISCONNECTED = "DESCONECTADO"
TEAM_STATUS_CONNECTED = "CONECTADO"

WORD_REQUEST_STATUS_QUEUED = "EN_COLA"
WORD_REQUEST_STATUS_TURN = "EN_TURNO"
WORD_REQUEST_STATUS_CORRECT = "CORRECTA"
WORD_REQUEST_STATUS_INCORRECT = "INCORRECTA"
WORD_REQUEST_STATUS_CANCELLED = "CANCELADA"

GAME_ANSWER_RESULT_CORRECT = "CORRECTA"
GAME_ANSWER_RESULT_INCORRECT = "INCORRECTA"

DEFAULT_GAME_CODE_LENGTH = 5
MIN_GAME_CODE_LENGTH = 3
MAX_GAME_CODE_LENGTH = 10
GAME_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

DEFAULT_GAME_TIME = 30
MIN_GAME_TIME = 5
MAX_GAME_TIME = 1800
GAME_TIME_INCREMENT = 5
DEFAULT_GAME_CORRECT_POINTS = 10
DEFAULT_GAME_INCORRECT_PENALTY = 0

JUDGE_USERNAME = "computacionz12"
JUDGE_PASSWORD = "juecesimbpc"

IMB_PC_TEAMS = (
    "Petapa",
    "Villa Nueva",
    "Antigua",
    "San Cristóbal",
    "Naranjo",
    "San Juan",
    "Amatitlán",
    "Aguilar Batres"
)

# Acciones compartidas por el cliente y el servidor de red
NETWORK_ACTION_PING = "ping"
NETWORK_ACTION_JOIN_GAME = "join_game"
NETWORK_ACTION_GET_GAME_STATE = "get_game_state"
NETWORK_ACTION_GET_STATISTICS_GAMES = "get_statistics_games"
NETWORK_ACTION_GET_LIVE_RANKING = "get_live_ranking"
NETWORK_ACTION_GET_CURRENT_QUESTION = "get_current_question"
NETWORK_ACTION_REQUEST_WORD = "request_word"
NETWORK_ACTION_DISCONNECT_PARTICIPANT = "disconnect_participant"

# Acciones del juez remoto
NETWORK_ACTION_JUDGE_GET_GAMES = "judge_get_games"
NETWORK_ACTION_JUDGE_GET_GAME_DETAIL = "judge_get_game_detail"
NETWORK_ACTION_JUDGE_GET_WAITING_ROOM = "judge_get_waiting_room"
NETWORK_ACTION_JUDGE_GET_LIVE_STATE = "judge_get_live_state"
NETWORK_ACTION_JUDGE_CHANGE_STATE = "judge_change_state"
NETWORK_ACTION_JUDGE_START_GAME = "judge_start_game"
NETWORK_ACTION_JUDGE_PAUSE_GAME = "judge_pause_game"
NETWORK_ACTION_JUDGE_RESUME_GAME = "judge_resume_game"
NETWORK_ACTION_JUDGE_ADVANCE_QUESTION = "judge_advance_question"
NETWORK_ACTION_JUDGE_MARK_TIME_EXPIRED = "judge_mark_time_expired"
NETWORK_ACTION_JUDGE_FINISH_GAME = "judge_finish_game"
NETWORK_ACTION_JUDGE_CANCEL_GAME = "judge_cancel_game"
NETWORK_ACTION_JUDGE_GIVE_WORD = "judge_give_word"
NETWORK_ACTION_JUDGE_MARK_CORRECT = "judge_mark_correct"
NETWORK_ACTION_JUDGE_MARK_INCORRECT = "judge_mark_incorrect"
NETWORK_ACTION_JUDGE_PASS_WORD = "judge_pass_word"
NETWORK_ACTION_JUDGE_DELETE_PARTICIPANT = "judge_delete_participant"
NETWORK_ACTION_JUDGE_GENERATE_GAME_CODE = "judge_generate_game_code"
NETWORK_ACTION_JUDGE_CREATE_GAME = "judge_create_game"
NETWORK_ACTION_JUDGE_CONTENT = "judge_content"
