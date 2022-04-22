import math
import obspython as obs

from pomodorotteux import Pomodorotteux, TwitchConfiguration


class Pomodoro:
    def __init__(
            self,
            time_session=0,
            time_pause=0,
            number_session=0,
            text_session="",
            text_time="",
            settings=None,
            red_tomato=None,
            green_tomato=None,
            ring=None,
            score_names=None,
            score_scores=None,
    ):
        self.time_session = time_session * 60
        self.time_pause = time_pause * 60
        self.number_session = number_session

        self.text_session = text_session
        self.text_time = text_time
        self.settings = settings

        self.is_in_initial_condition = True
        self.is_in_session = False
        self.current_session = 0
        self.elapsed_time = 0
        self.finished = False
        self.can_pause = False
        self.is_running = False

        self.red_tomato = red_tomato
        self.green_tomato = green_tomato
        self.ring = ring
        obs.obs_sceneitem_set_visible(self.red_tomato, False)
        obs.obs_sceneitem_set_visible(self.ring, False)
        obs.obs_sceneitem_set_visible(self.green_tomato, True)

        self.pomodorotteux = None
        self.score_names = score_names
        self.score_scores = score_scores

    def total_time(self):
        if self.is_in_session:
            return self.time_session
        else:
            return self.time_pause

    def toggle_type(self):
        self.is_in_initial_condition = False
        self.is_in_session = not self.is_in_session
        if self.is_in_session:
            self.current_session += 1
            obs.obs_sceneitem_set_visible(self.red_tomato, False)
            obs.obs_sceneitem_set_visible(self.ring, False)
            obs.obs_sceneitem_set_visible(self.green_tomato, True)
        else:
            obs.obs_sceneitem_set_visible(self.red_tomato, True)
            obs.obs_sceneitem_set_visible(self.ring, True)
            obs.obs_sceneitem_set_visible(self.green_tomato, False)
            if self.pomodorotteux:
                self.pomodorotteux.add_tomato_to_connected_users()
            if self.number_session == self.current_session:
                self.finished = True
                if self.pomodorotteux:
                    self.pomodorotteux.end_session()
        self.elapsed_time = 0

    def prepare_session(self):
        self.is_in_initial_condition = True
        self.is_in_session = False
        self.current_session = 0
        self.elapsed_time = 0
        self.finished = False
        self.can_pause = True
        self.is_running = False

    def start_timer(self, func, new_session):
        if new_session:
            self.prepare_session()
        obs.timer_add(func, 1000)
        pomodoro.is_running = True

    def stop_timer(self, func, reset_timer):
        obs.timer_remove(func)
        if reset_timer:
            self.elapsed_time = 0
        pomodoro.is_running = False
        if pomodoro.pomodorotteux:
            self.pomodorotteux.end_session()

    def pause_resume_timer(self, func):
        if not self.can_pause:
            return
        if pomodoro.is_running:
            self.stop_timer(func, False)
        else:
            self.start_timer(func, False)


pomodoro = Pomodoro()


def get_time_in_text(remaining_time):
    seconds = math.floor(remaining_time % 60)
    seconds = f"{seconds}" if seconds >= 10 else f"0{seconds}"
    minutes = math.floor(remaining_time / 60)
    if minutes < 10:
        return f" {minutes}:{seconds}"
    else:
        return f"{minutes}:{seconds}"


def advance_time():
    global pomodoro

    if pomodoro.text_session is None or pomodoro.text_session is None:
        return

    if pomodoro.is_in_initial_condition or pomodoro.total_time() - pomodoro.elapsed_time < 1:
        pomodoro.toggle_type()
        if pomodoro.is_in_session:
            text_session = f"Session {pomodoro.current_session}/{pomodoro.number_session}"
        else:
            text_session = "    Pause!"
        obs.obs_data_set_string(pomodoro.settings, "text", text_session)
        obs.obs_source_update(pomodoro.text_session, pomodoro.settings)

    if pomodoro.finished:
        obs.obs_data_set_string(pomodoro.settings, "text", " 0:00")
        obs.obs_source_update(pomodoro.text_time, pomodoro.settings)

        obs.obs_data_set_string(pomodoro.settings, "text", "    Bravo!")
        obs.obs_source_update(pomodoro.text_session, pomodoro.settings)
        obs.timer_remove(advance_time)
    else:
        text_to_print = get_time_in_text(pomodoro.total_time() - pomodoro.elapsed_time)
        pomodoro.elapsed_time += 1

        obs.obs_data_set_string(pomodoro.settings, "text", text_to_print)
        obs.obs_source_update(pomodoro.text_time, pomodoro.settings)


def stop_timer(props, prop):
    global pomodoro

    pomodoro.stop_timer(advance_time, reset_timer=True)
    if pomodoro.text_session is None or pomodoro.text_session is None:
        return

    obs.obs_data_set_string(pomodoro.settings, "text", get_time_in_text(pomodoro.time_session))
    obs.obs_source_update(pomodoro.text_time, pomodoro.settings)

    obs.obs_data_set_string(pomodoro.settings, "text", "Bienvenue!")
    obs.obs_source_update(pomodoro.text_session, pomodoro.settings)

    if pomodoro.pomodorotteux:
        pomodoro.pomodorotteux.end_session()


def pause_timer(props, prop):
    global pomodoro
    pomodoro.pause_resume_timer(advance_time)


def score_update_callback(scores: dict):
    global pomodoro
    score_names = ""
    score_scores = ""
    scores_sorted = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
    for name in scores_sorted:
        score_names += name + "\n"
        score_scores += str(scores_sorted[name]) + "\n"

    obs.obs_data_set_string(pomodoro.settings, "text", score_names)
    obs.obs_source_update(pomodoro.score_names, pomodoro.settings)

    obs.obs_data_set_string(pomodoro.settings, "text", score_scores)
    obs.obs_source_update(pomodoro.score_scores, pomodoro.settings)


def has_connected_callback(name: str, tomato_done: dict):
    global pomodoro
    if tomato_done[name] == 0:
        pomodoro.pomodorotteux.post_message(
            f"Message de la tomate : {name} s'est connecté(e) pour la première fois! "
            f"La gang des Pomodorotteuses(eux) te souhaitent la bienvenue parmi nous!"
        )
    else:
        pomodoro.pomodorotteux.post_message(
            f"Message de la tomate : {name} s'est connecté(e) aux tomates! Bon travail!"
        )


def disconnect_user_callback(name: str):
    global pomodoro
    pomodoro.pomodorotteux.post_message(f"Message de la tomate : {name} a été bien silencieux(se)! Tu es toujours là?")


def start_timer(props, prop):
    global pomodoro

    stop_timer(None, None)
    if start_timer and pomodoro.text_session != "" and pomodoro.text_time != "":
        pomodoro.start_timer(advance_time, new_session=True)

    try:
        pomodoro.pomodorotteux = Pomodorotteux(
            TwitchConfiguration.load_configuration("my_config_file.key"),
            has_connected_callback=has_connected_callback,
            disconnect_user_callback=disconnect_user_callback,
            score_update_callback=score_update_callback,
            ping_time=90*60,
        )
    except:
        # Just ignore the props if it fails for any reason
        pomodoro.pomodorotteux = None


def script_description():
    return "Countdown for Pomodoro sessions\nBy Pariterre"


def script_update(settings):
    global pomodoro
    if pomodoro.pomodorotteux:
        pomodoro.pomodorotteux.end_session()

    time_session = obs.obs_data_get_int(settings, "time_pomodoro")
    time_pause = obs.obs_data_get_int(settings, "time_pause")
    number_session = obs.obs_data_get_int(settings, "number_session")
    text_session = obs.obs_get_source_by_name(obs.obs_data_get_string(settings, "text_session"))
    text_time = obs.obs_get_source_by_name(obs.obs_data_get_string(settings, "text_time"))

    score_names = obs.obs_get_source_by_name(obs.obs_data_get_string(settings, "score_names"))
    score_scores = obs.obs_get_source_by_name(obs.obs_data_get_string(settings, "score_scores"))

    scene = obs.obs_get_scene_by_name(obs.obs_data_get_string(settings, "pomodoro_scene"))
    red_tomato = obs.obs_scene_find_source_recursive(scene, obs.obs_data_get_string(settings, "red_tomato"))
    green_tomato = obs.obs_scene_find_source_recursive(scene, obs.obs_data_get_string(settings, "green_tomato"))
    ring = obs.obs_scene_find_source_recursive(scene, obs.obs_data_get_string(settings, "ring"))

    settings = obs.obs_data_create()
    pomodoro = Pomodoro(time_session, time_pause, number_session, text_session, text_time, settings, red_tomato, green_tomato, ring, score_names, score_scores)

    stop_timer(None, None)


def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "time_pomodoro", 0)
    obs.obs_data_set_default_int(settings, "time_pause", 0)


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_int(props, "time_pomodoro", "Pomodoro time", 0, 60, 1)
    obs.obs_properties_add_int(props, "time_pause", "Pause time", 0, 60, 1)
    obs.obs_properties_add_int(props, "number_session", "Number of sessions", 0, 60, 1)

    obs.obs_properties_add_button(props, "start_button", "Start", start_timer)
    obs.obs_properties_add_button(props, "pause_button", "Pause/Resume", pause_timer)
    obs.obs_properties_add_button(props, "stop_button", "Stop", stop_timer)

    p_scene = obs.obs_properties_add_list(
        props, "pomodoro_scene", "Scene", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_pomodoro = obs.obs_properties_add_list(
        props, "text_session", "Pomodoro session", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_time = obs.obs_properties_add_list(
        props, "text_time", "Pomodoro time", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_red_tomato = obs.obs_properties_add_list(
        props, "red_tomato", "Red tomato", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_green_tomato = obs.obs_properties_add_list(
        props, "green_tomato", "Green tomato", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_ring = obs.obs_properties_add_list(
        props, "ring", "Ring", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_score_names = obs.obs_properties_add_list(
        props, "score_names", "Pomodoro Hall of fame", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    p_scores = obs.obs_properties_add_list(
        props, "score_scores", "Pomodoro Score", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if source_id == "text_gdiplus" or source_id == "text_ft2_source" or source_id == "text_pango_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p_pomodoro, name, name)
                obs.obs_property_list_add_string(p_time, name, name)
                obs.obs_property_list_add_string(p_score_names, name, name)
                obs.obs_property_list_add_string(p_scores, name, name)
            elif source_id == "image_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p_red_tomato, name, name)
                obs.obs_property_list_add_string(p_green_tomato, name, name)
            elif source_id == "ffmpeg_source":
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p_ring, name, name)
        obs.source_list_release(sources)

    scenes = obs.obs_frontend_get_scene_names()
    for scene in scenes:
        obs.obs_property_list_add_string(p_scene, scene, scene)

    return props
