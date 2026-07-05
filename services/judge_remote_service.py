from logical_business.partida_business import PartidaBusiness
from services.remote_content_services import WebContentServices


class JudgeWebService(PartidaBusiness):

    is_remote = False

    def __init__(self):
        super().__init__()
        self.content_services = WebContentServices()
