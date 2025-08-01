#ifndef LEGOGAMESTATE_H
#define LEGOGAMESTATE_H

#include "actionsfwd.h"
#include "decomp.h"
#include "mxtypes.h"
#include "mxvariable.h"

#include <string.h>

class LegoFile;
class LegoState;
class LegoStorage;
class MxVariableTable;
class MxString;

extern const char* g_actorNames[7];

// SIZE 0x08
struct ColorStringStruct {
	const char* m_targetName; // 0x00
	const char* m_colorName;  // 0x04
};

// VTABLE: LEGO1 0x100d74a8
// VTABLE: BETA10 0x101bc4f0
// SIZE 0x30
class LegoBackgroundColor : public MxVariable {
public:
	LegoBackgroundColor();
	LegoBackgroundColor(const char* p_key, const char* p_value);

	void SetValue(const char* p_colorString) override; // vtable+0x04

	void SetLightColor(float p_r, float p_g, float p_b);
	void SetLightColor();
	void ToggleDayNight(MxBool p_sun);
	void ToggleSkyColor();

private:
	float m_h; // 0x24
	float m_s; // 0x28
	float m_v; // 0x2c
};

// VTABLE: LEGO1 0x100d74b8
// VTABLE: BETA10 0x101bc500
// SIZE 0x24
class LegoFullScreenMovie : public MxVariable {
public:
	LegoFullScreenMovie();
	LegoFullScreenMovie(const char* p_key, const char* p_value);

	void SetValue(const char* p_option) override; // vtable+0x04
};

// SIZE 0x430
class LegoGameState {
public:
	enum Act {
		e_actNotFound = -1,
		e_act1,
		e_act2,
		e_act3
	};

	enum Area {
		e_undefined = 0,
		e_previousArea = 0,
		e_isle,
		e_infomain,
		e_infodoor,
		e_infocenterExited,
		e_elevbott,
		e_elevride,
		e_elevride2,
		e_elevopen,
		e_seaview,
		e_observe,
		e_elevdown,
		e_regbook,
		e_infoscor,
		e_jetrace,
		e_jetrace2,
		e_jetraceExterior,
		e_jetskibuildExited,
		e_carrace,
		e_carraceExterior,
		e_racecarbuildExited,
		e_unk21,
		e_pizzeriaExterior,
		e_unk23,
		e_unk24,
		e_garageExterior,
		e_garage,
		e_garadoor,
		e_garageExited,
		e_hospitalExterior,
		e_hospital,
		e_hospitalExited,
		e_policeExterior,
		e_policeExited,
		e_police,
		e_polidoor,
		e_copterbuild,
		e_dunecarbuild,
		e_jetskibuild,
		e_racecarbuild,
		e_helicopterSpawn,
		e_unk41,
		e_unk42,
		e_dunebuggySpawn,
		e_racecarSpawn,
		e_jetskiSpawn,
		e_act2main,
		e_act3script,
		e_unk48,
		e_unk49,
		e_unk50,
		e_unk51,
		e_towTrackHookedUp,
		e_jukeboxw,
		e_jukeboxExterior,
		e_unk55,
		e_histbook,
		e_bike,
		e_dunecar,
		e_motocycle,
		e_copter,
		e_skateboard,
		e_ambulance,
		e_towtrack,
		e_jetski,

		e_vehicleExited = 66
	};

	// SIZE 0x0e
	struct Username {
		Username();
		void Set(Username& p_other) { memcpy(m_letters, p_other.m_letters, sizeof(m_letters)); }

		MxResult Serialize(LegoStorage* p_storage);
		Username& operator=(const Username& p_other);

		MxS16 m_letters[7]; // 0x00
	};

	// SIZE 0x2c
	struct ScoreItem {
		MxResult Serialize(LegoStorage* p_storage);

		MxS16 m_totalScore;  // 0x00
		MxU8 m_scores[5][5]; // 0x02
		Username m_name;     // 0x1c
		MxS16 m_playerId;    // 0x2a

		ScoreItem& operator=(const ScoreItem& p_other)
		{
			// MSVC auto-generates an operator=, but LegoGameState::WriteScoreHistory() has a much better match
			// with a manual implementation.
			m_totalScore = p_other.m_totalScore;
			memcpy(m_scores, p_other.m_scores, sizeof(m_scores));
			m_name = p_other.m_name;
			m_playerId = p_other.m_playerId;
			return *this;
		}
	};

	// SIZE 0x372
	struct History {
		History();
		void WriteScoreHistory();
		MxResult Serialize(LegoStorage* p_storage);
		ScoreItem* FindPlayerInScoreHistory(Username* p_player, MxS16 p_unk0x24, MxS32& p_unk0x2c);

		// FUNCTION: BETA10 0x1002c2b0
		MxS16 GetCount() { return m_count; }

		// TODO: Not yet correct
		// FUNCTION: BETA10 0x1002c540
		ScoreItem* GetScore(MxS32 p_index) { return p_index >= m_count ? NULL : &m_scores[p_index]; }

		MxS16 m_count; // 0x00
#ifdef BETA10
		MxS16 m_indices[20]; // 0x02
#endif
		ScoreItem m_scores[20]; // 0x02 (0x22 for BETA10)
		MxS16 m_nextPlayerId;   // 0x372 (0x392 for BETA10)
	};

	LegoGameState();
	~LegoGameState();

	void SetActor(MxU8 p_actorId);
	void RemoveActor();
	void ResetROI();

	MxResult Save(MxULong);
	MxResult DeleteState();
	MxResult Load(MxULong);

	void SerializePlayersInfo(MxS16 p_flags);
	MxResult AddPlayer(Username& p_player);
	void SwitchPlayer(MxS16 p_playerId);
	MxS16 FindPlayer(Username& p_player);

	void SerializeScoreHistory(MxS16 p_flags);
	void SetSavePath(char*);

	LegoState* GetState(const char* p_stateName);
	LegoState* CreateState(const char* p_stateName);

	void GetFileSavePath(MxString* p_outPath, MxS16 p_slotn);
	void StopArea(Area p_area);
	void SwitchArea(Area p_area);
	void Init();

	// FUNCTION: BETA10 0x10083ff5
	MxU8 GetActorId() { return m_actorId; }

	// FUNCTION: BETA10 0x1004a2d0
	const char* GetActorName() { return g_actorNames[GetActorId()]; }

	// FUNCTION: BETA10 0x1002b4c0
	Act GetCurrentAct() { return m_currentAct; }

	Act GetLoadedAct() { return m_loadedAct; }

	void SetActorId(MxU8 p_actorId) { m_actorId = p_actorId; }
	LegoBackgroundColor* GetBackgroundColor() { return m_backgroundColor; }

	void SetCurrentAct(Act p_currentAct);
	void FindLoadedAct();
	void RegisterState(LegoState* p_state);

private:
	MxResult WriteVariable(LegoStorage* p_storage, MxVariableTable* p_from, const char* p_variableName);
	MxResult WriteEndOfVariables(LegoStorage* p_storage);
	MxS32 ReadVariable(LegoStorage* p_storage, MxVariableTable* p_to);
	void SetColors();
	void SetROIColorOverride();

	char* m_savePath;                           // 0x00
	MxS16 m_stateCount;                         // 0x04
	LegoState** m_stateArray;                   // 0x08
	MxU8 m_actorId;                             // 0x0c
	Act m_currentAct;                           // 0x10
	Act m_loadedAct;                            // 0x14
	LegoBackgroundColor* m_backgroundColor;     // 0x18
	LegoBackgroundColor* m_tempBackgroundColor; // 0x1c
	LegoFullScreenMovie* m_fullScreenMovie;     // 0x20

public:
	MxS16 m_currentPlayerId;              // 0x24
	MxS16 m_playerCount;                  // 0x26
	Username m_players[9];                // 0x28
	History m_history;                    // 0xa6
	JukeboxScript::Script m_jukeboxMusic; // 0x41c
	MxBool m_isDirty;                     // 0x420
	Area m_currentArea;                   // 0x424
	Area m_previousArea;                  // 0x428
	Area m_unk0x42c;                      // 0x42c
};

MxBool ROIColorOverride(const char* p_input, char* p_output, MxU32 p_copyLen);

// SYNTHETIC: LEGO1 0x1003c860
// LegoGameState::ScoreItem::ScoreItem

#endif // LEGOGAMESTATE_H
