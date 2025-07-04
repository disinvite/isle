#include "modeldb.h"

DECOMP_SIZE_ASSERT(ModelDbWorld, 0x18)
DECOMP_SIZE_ASSERT(ModelDbPart, 0x18)
DECOMP_SIZE_ASSERT(ModelDbModel, 0x38)
DECOMP_SIZE_ASSERT(ModelDbPartList, 0x1c)
DECOMP_SIZE_ASSERT(ModelDbPartListCursor, 0x10)

// FUNCTION: LEGO1 0x10027690
// FUNCTION: BETA10 0x100e5620
void ModelDbModel::Free()
{
	delete[] m_modelName;
	delete[] m_presenterName;
}

// FUNCTION: LEGO1 0x100276b0
MxResult ModelDbModel::Read(FILE* p_file)
{
	MxU32 len;

	if (fread(&len, sizeof(MxU32), 1, p_file) != 1) {
		return FAILURE;
	}

	m_modelName = new char[len];
	if (fread(m_modelName, len, 1, p_file) != 1) {
		return FAILURE;
	}

	if (fread(&m_modelDataLength, sizeof(MxU32), 1, p_file) != 1) {
		return FAILURE;
	}
	if (fread(&m_modelDataOffset, sizeof(MxU32), 1, p_file) != 1) {
		return FAILURE;
	}
	if (fread(&len, sizeof(MxU32), 1, p_file) != 1) {
		return FAILURE;
	}

	m_presenterName = new char[len];
	if (fread(m_presenterName, len, 1, p_file) != 1) {
		return FAILURE;
	}

	if (fread(&m_location, sizeof(float), 3, p_file) != 3) {
		return FAILURE;
	}
	if (fread(&m_direction, sizeof(float), 3, p_file) != 3) {
		return FAILURE;
	}
	if (fread(&m_up, sizeof(float), 3, p_file) != 3) {
		return FAILURE;
	}
	if (fread(&m_visible, sizeof(MxU8), 1, p_file) != 1) {
		return FAILURE;
	}

	return SUCCESS;
}

// FUNCTION: LEGO1 0x10027850
MxResult ModelDbPart::Read(FILE* p_file)
{
	MxU32 len;
	char buff[128];

	if (fread(&len, sizeof(MxU32), 1, p_file) != 1) {
		return FAILURE;
	}

	// (modernization) critical bug: buffer overrun
	if (fread(buff, len, 1, p_file) != 1) {
		return FAILURE;
	}

	m_roiName = buff;

	if (fread(&m_partDataLength, sizeof(undefined4), 1, p_file) != 1) {
		return FAILURE;
	}
	if (fread(&m_partDataOffset, sizeof(undefined4), 1, p_file) != 1) {
		return FAILURE;
	}

	return SUCCESS;
}

// FUNCTION: LEGO1 0x10027910
MxResult ReadModelDbWorlds(FILE* p_file, ModelDbWorld*& p_worlds, MxS32& p_numWorlds)
{
	p_worlds = NULL;
	p_numWorlds = 0;

	MxS32 numWorlds;
	if (fread(&numWorlds, sizeof(numWorlds), 1, p_file) != 1) {
		return FAILURE;
	}

	ModelDbWorld* worlds = new ModelDbWorld[numWorlds];
	MxS32 worldNameLen, numParts, i, j;

	for (i = 0; i < numWorlds; i++) {
		if (fread(&worldNameLen, sizeof(MxS32), 1, p_file) != 1) {
			return FAILURE;
		}

		worlds[i].m_worldName = new char[worldNameLen];
		if (fread(worlds[i].m_worldName, worldNameLen, 1, p_file) != 1) {
			return FAILURE;
		}

		if (fread(&numParts, sizeof(MxS32), 1, p_file) != 1) {
			return FAILURE;
		}

		worlds[i].m_partList = new ModelDbPartList();

		for (j = 0; j < numParts; j++) {
			ModelDbPart* part = new ModelDbPart();

			if (part->Read(p_file) != SUCCESS) {
				return FAILURE;
			}

			worlds[i].m_partList->Append(part);
		}

		if (fread(&worlds[i].m_numModels, sizeof(MxS32), 1, p_file) != 1) {
			return FAILURE;
		}

		worlds[i].m_models = new ModelDbModel[worlds[i].m_numModels];

		for (j = 0; j < worlds[i].m_numModels; j++) {
			if (worlds[i].m_models[j].Read(p_file) != SUCCESS) {
				return FAILURE;
			}
		}
	}

	p_worlds = worlds;
	p_numWorlds = numWorlds;
	return SUCCESS;
}

// FUNCTION: LEGO1 0x10028080
// FUNCTION: BETA10 0x100e6431
void FreeModelDbWorlds(ModelDbWorld*& p_worlds, MxS32 p_numWorlds)
{
	ModelDbWorld* worlds = p_worlds;

	for (MxS32 i = 0; i < p_numWorlds; i++) {
		delete[] worlds[i].m_worldName;

		ModelDbPartListCursor cursor(worlds[i].m_partList);
		ModelDbPart* part;

		while (cursor.Next(part)) {
			delete part;
		}

		delete worlds[i].m_partList;

		ModelDbModel* models = worlds[i].m_models;
		for (MxS32 j = 0; j < worlds[i].m_numModels; j++) {
			models[j].Free();
		}

		delete[] worlds[i].m_models;
	}

	delete[] p_worlds;
	p_worlds = NULL;
}
