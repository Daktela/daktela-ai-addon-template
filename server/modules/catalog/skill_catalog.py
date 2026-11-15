from typing import override

from cw_addons.modules.models import LangString, MessageAction, ModuleResponses, SkillsAttribute, SkillSummary
from cw_addons.modules.module import Module
from pydantic import BaseModel


class SkillCatalogAttributes(BaseModel):
    skills: list[SkillSummary] = []


class SkillCatalogModule(Module[SkillCatalogAttributes]):
    name = "skill_catalog"
    version = "v1"
    public = True
    icon = "📚"
    title = LangString(en="Skill catalog example", cs="Příklad katalogu skillů")
    category = LangString(en="Examples", cs="Příklady")
    short_description = LangString(en="Shows selected skill summaries", cs="Zobrazí vybrané skilly")
    description = short_description
    input_attributes = [SkillsAttribute(name="skills")]

    @override
    async def execute(self) -> ModuleResponses:
        return ModuleResponses(actions=[MessageAction(text=", ".join(skill.name for skill in self.attributes.skills))])
