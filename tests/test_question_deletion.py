import sys
import types
import unittest

try:
    import psycopg2  # noqa: F401
except ModuleNotFoundError:
    pregunta_dao_module = types.ModuleType("dao.pregunta_dao")


    class PlaceholderPreguntaDao:
        pass


    pregunta_dao_module.PreguntaDao = PlaceholderPreguntaDao
    sys.modules["dao.pregunta_dao"] = pregunta_dao_module

from logical_business.pregunta_business import PreguntaBusiness


class FakePreguntaDao:

    def __init__(self, game_uses=0, delete_success=True):
        self.game_uses = game_uses
        self.delete_success = delete_success
        self.delete_calls = []

    def count_game_uses(self, id_pregunta):
        return self.game_uses

    def delete(self, id_pregunta):
        self.delete_calls.append(id_pregunta)
        return self.delete_success


class PreguntaBusinessDeleteTests(unittest.TestCase):

    def business_with_dao(self, dao):
        business = PreguntaBusiness()
        business._PreguntaBusiness__pregunta_dao = dao
        return business

    def test_rejects_question_already_used_in_game(self):
        dao = FakePreguntaDao(game_uses=1)
        result = self.business_with_dao(dao).delete(42)

        self.assertFalse(result.get_success())
        self.assertEqual(
            result.get_message(),
            "Esta pregunta no puede eliminarse porque ya fue utilizada en una partida."
        )
        self.assertEqual(dao.delete_calls, [])

    def test_deletes_question_without_game_history(self):
        dao = FakePreguntaDao(game_uses=0, delete_success=True)
        result = self.business_with_dao(dao).delete(42)

        self.assertTrue(result.get_success())
        self.assertEqual(result.get_message(), "Pregunta eliminada correctamente.")
        self.assertEqual(dao.delete_calls, [42])

    def test_reports_late_game_relation_after_failed_delete(self):
        class LateRelationDao(FakePreguntaDao):

            def count_game_uses(self, id_pregunta):
                return 0 if not self.delete_calls else 1

        dao = LateRelationDao(delete_success=False)
        result = self.business_with_dao(dao).delete(42)

        self.assertFalse(result.get_success())
        self.assertEqual(
            result.get_message(),
            "Esta pregunta no puede eliminarse porque ya fue utilizada en una partida."
        )


if __name__ == "__main__":
    unittest.main()
