"""Offline checks for curriculum editing; no sockets or student data writes."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.schema import validate_curriculum


class CurriculumValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum = json.loads((ROOT / 'data/curriculum.json').read_text())

    def changed(self):
        data = copy.deepcopy(self.curriculum)
        return data, data['lessons'][2]

    def test_complete_course_is_valid(self):
        self.assertEqual(validate_curriculum(self.curriculum), [])
        self.assertEqual([l['number'] for l in self.curriculum['lessons']], list(range(1, 21)))

    def test_malformed_teaching_objects_are_rejected(self):
        for field in ['pedagogy', 'liveListening']:
            for value in [None, 'broken', []]:
                with self.subTest(field=field, value=value):
                    data, lesson = self.changed()
                    lesson[field] = value
                    self.assertTrue(validate_curriculum(data))

    def test_learning_sequence_duration_is_consistent(self):
        for value in [0, -1, True, '20']:
            with self.subTest(minutes=value):
                data, lesson = self.changed()
                lesson['pedagogy']['sequence'][0]['minutes'] = value
                self.assertTrue(validate_curriculum(data))
        data, lesson = self.changed()
        lesson['minutes'] += 1
        self.assertTrue(validate_curriculum(data))

    def test_decisions_and_listening_references_are_validated(self):
        data, lesson = self.changed()
        lesson['pedagogy']['decisions'][0]['sourceRefs'] = ['zt-99-slide-999']
        self.assertTrue(validate_curriculum(data))
        data, lesson = self.changed()
        lesson['pedagogy']['decisions'].pop()
        self.assertTrue(validate_curriculum(data))
        data, lesson = self.changed()
        lesson['liveListening']['questionId'] = 'missing-question'
        self.assertTrue(validate_curriculum(data))

    def test_task_scaffolds_and_discussion_guides_are_required(self):
        for field in ['scaffold', 'successCriteria']:
            data, lesson = self.changed()
            lesson['tasks'][0][field] = []
            self.assertTrue(validate_curriculum(data))
        data, lesson = self.changed()
        lesson['readings'][0]['discussion'][0]['guide'] = ''
        self.assertTrue(validate_curriculum(data))

    def test_invalid_keys_and_task_criteria_are_rejected(self):
        data, lesson = self.changed()
        lesson['questions'][0]['answer'] = 'absent-option'
        self.assertTrue(validate_curriculum(data))
        data, lesson = self.changed()
        lesson['tasks'][0]['criteria'] = ['unrecognized-dimension']
        self.assertTrue(validate_curriculum(data))


if __name__ == '__main__':
    unittest.main(verbosity=2)
