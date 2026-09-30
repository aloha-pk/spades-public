# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org


from pyspades.contained import WeaponReload, SetTool, PlayerPropertiesV1
from piqueserver.commands import command
from pyspades.constants import FALL_KILL, GRENADE_TOOL
set_tool = SetTool()

COMMAND_IS_LOUD = False
INFINITE_BLOCKS = True

@command("iblox", admin_only=True)
def infiniteblocks(connection):
    global INFINITE_BLOCKS
    INFINITE_BLOCKS = not INFINITE_BLOCKS
    on_off = 'ON' if INFINITE_BLOCKS else 'OFF'

    connection.protocol.irc_say(f"* {connection.name} has toggled infinite blocks {on_off}")

    ingame_msg = f"Infinite blocks have been toggled {on_off}!"

    if COMMAND_IS_LOUD:
        connection.protocol.send_chat(ingame_msg)
    else:
        return ingame_msg


def apply_script(protocol, connection, config):
    class InfiBlocksConnection(connection):
        def infiblocks_refill(self):
            if PlayerPropertiesV1.ext_id in self.proto_extensions and \
               self.proto_extensions[PlayerPropertiesV1.ext_id] == PlayerPropertiesV1.ext_version:
                properties = PlayerPropertiesV1()
                properties.player_id = self.player_id
                properties.health = self.hp
                properties.blocks = self.blocks = 50
                properties.grenades = self.grenades
                properties.ammo_clip = self.weapon_object.current_ammo
                properties.ammo_reserved = self.weapon_object.current_stock
                properties.score = self.kills
                self.send_contained(properties)
                return

            health = self.hp
            weapon = self.weapon_object
            ammo = weapon.current_ammo
            reserve = weapon.current_stock
            grenades = self.grenades
            self.refill()
            self.set_hp(health, kill_type=FALL_KILL)
            self.grenades = grenades
            weapon.set_shoot(False)
            weapon.current_stock = reserve
            weapon.current_ammo = ammo
            weapon_reload = WeaponReload()
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = weapon.current_ammo
            weapon_reload.reserve_ammo = weapon.current_stock
            self.send_contained(weapon_reload)

        def on_block_build(self, x, y, z):
            if INFINITE_BLOCKS and self.blocks <= 5:
                self.infiblocks_refill()
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if INFINITE_BLOCKS and self.blocks <= 25:
                self.infiblocks_refill()
            return connection.on_line_build(self, points)

        def on_tool_set_attempt(self, tool):
            if tool == GRENADE_TOOL and self.grenades <= 0:
                set_tool.player_id = self.player_id
                set_tool.value = self.tool
                self.send_contained(set_tool)
                if self.client_info:
                    if self.client_info["client"] == "OpenSpades":
                        self.send_chat_error("Out of Grenades")
                return False
            return connection.on_tool_set_attempt(self, tool)

    return protocol, InfiBlocksConnection
