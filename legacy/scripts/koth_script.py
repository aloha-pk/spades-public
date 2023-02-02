# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import Territory

locations = ((256, 256), (256, 256), (256, 256), (256, 256))

def apply_script(protocol, connection, config):
    class CPProtocol(protocol):
        def get_cp_entities(self):
            entities = []
            for i, (x, y) in enumerate(locations):
                entity = Territory(i, self, *(x, y, self.map.get_z(x, y)))
                if i % 2 == 0:
                    entity.team = self.blue_team
                    self.blue_team.cp = entity
                    self.blue_team.spawn_cp = entity
                    self.blue_team.cp.disabled = False
                else:
                    entity.team = self.green_team
                    self.green_team.cp = entity
                    self.green_team.spawn_cp = entity
                    self.green_team.cp.disabled = False
                entities.append(entity)
            return entities
    return CPProtocol, connection
