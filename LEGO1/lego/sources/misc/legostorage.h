#ifndef __LEGOSTORAGE_H
#define __LEGOSTORAGE_H

#include "legotypes.h"
#include "mxgeometry/mxgeometry3d.h"
#include "mxstring.h"

#include <stdio.h>

// VTABLE: LEGO1 0x100d7d80
// VTABLE: BETA10 0x101bb1c8
// SIZE 0x08
class LegoStorage {
public:
	enum OpenFlags {
		c_read = 1,
		c_write = 2,
		c_text = 4
	};

	LegoStorage() : m_mode(0) {}

	// FUNCTION: LEGO1 0x10045ad0
	// FUNCTION: BETA10 0x10056e10
	virtual ~LegoStorage() {}

	virtual LegoResult Read(void* p_buffer, LegoU32 p_size) = 0;        // vtable+0x04
	virtual LegoResult Write(const void* p_buffer, LegoU32 p_size) = 0; // vtable+0x08
	virtual LegoResult GetPosition(LegoU32& p_position) = 0;            // vtable+0x0c
	virtual LegoResult SetPosition(LegoU32 p_position) = 0;             // vtable+0x10

	// FUNCTION: LEGO1 0x10045ae0
	// FUNCTION: BETA10 0x10056e40
	virtual LegoBool IsWriteMode() { return m_mode == c_write; } // vtable+0x14

	// FUNCTION: LEGO1 0x10045af0
	// FUNCTION: BETA10 0x10056e80
	virtual LegoBool IsReadMode() { return m_mode == c_read; } // vtable+0x18

	// FUNCTION: BETA10 0x1004b190
	LegoStorage* ReadByte(void* p_buffer)
	{
		Read(p_buffer, 1);
		return this;
	}

	// FUNCTION: BETA10 0x10024680
	LegoStorage* ReadWord(void* p_buffer)
	{
		Read(p_buffer, 2);
		return this;
	}

	// FUNCTION: BETA10 0x10088580
	LegoStorage* ReadDword(void* p_buffer)
	{
		Read(p_buffer, 4);
		return this;
	}

	// FUNCTION: BETA10 0x1004b0d0
	LegoStorage* WriteByte(const LegoU8 p_value)
	{
		Write(&p_value, 1);
		return this;
	}

	// FUNCTION: BETA10 0x10017ce0
	LegoStorage* WriteWord(const LegoU16 p_value)
	{
		Write(&p_value, 2);
		return this;
	}

	// FUNCTION: BETA10 0x10088540
	LegoStorage* WriteDword(const LegoU32 p_value)
	{
		Write(&p_value, 4);
		return this;
	}

	// SYNTHETIC: LEGO1 0x10045b00
	// SYNTHETIC: BETA10 0x10056ec0
	// LegoStorage::`scalar deleting destructor'

protected:
	LegoU8 m_mode; // 0x04
};

template <class T>
inline void Read(LegoStorage* p_storage, T* p_variable, LegoU32 p_size = sizeof(T))
{
	p_storage->Read(p_variable, p_size);
}

template <class T>
inline void Write(LegoStorage* p_storage, T p_variable)
{
	p_storage->Write(&p_variable, sizeof(p_variable));
}

// VTABLE: LEGO1 0x100db710
// SIZE 0x10
class LegoMemory : public LegoStorage {
public:
	LegoMemory(void* p_buffer);
	LegoResult Read(void* p_buffer, LegoU32 p_size) override;        // vtable+0x04
	LegoResult Write(const void* p_buffer, LegoU32 p_size) override; // vtable+0x08

	// FUNCTION: LEGO1 0x100994a0
	LegoResult GetPosition(LegoU32& p_position) override // vtable+0x0c
	{
		p_position = m_position;
		return SUCCESS;
	}

	// FUNCTION: LEGO1 0x100994b0
	LegoResult SetPosition(LegoU32 p_position) override // vtable+0x10
	{
		m_position = p_position;
		return SUCCESS;
	}

	// SYNTHETIC: LEGO1 0x10045a80
	// LegoMemory::~LegoMemory

	// SYNTHETIC: LEGO1 0x100990f0
	// LegoMemory::`scalar deleting destructor'

protected:
	LegoU8* m_buffer;   // 0x04
	LegoU32 m_position; // 0x08
};

// VTABLE: LEGO1 0x100db730
// VTABLE: BETA10 0x101c37c0
// SIZE 0x0c
class LegoFile : public LegoStorage {
public:
	LegoFile();
	~LegoFile() override;
	LegoResult Read(void* p_buffer, LegoU32 p_size) override;        // vtable+0x04
	LegoResult Write(const void* p_buffer, LegoU32 p_size) override; // vtable+0x08
	LegoResult GetPosition(LegoU32& p_position) override;            // vtable+0x0c
	LegoResult SetPosition(LegoU32 p_position) override;             // vtable+0x10
	LegoResult Open(const char* p_name, LegoU32 p_mode);

	// FUNCTION: LEGO1 0x100343d0
	LegoStorage* WriteVector3(Mx3DPointFloat p_vec3)
	{
		float data = p_vec3[0];
		Write(&data, sizeof(float));

		data = p_vec3[1];
		Write(&data, sizeof(float));

		data = p_vec3[2];
		Write(&data, sizeof(float));
		return this;
	}

	// FUNCTION: LEGO1 0x10034430
	LegoStorage* ReadVector3(Mx3DPointFloat& p_vec3)
	{
		Read(&p_vec3[0], sizeof(float));
		Read(&p_vec3[1], sizeof(float));
		Read(&p_vec3[2], sizeof(float));
		return this;
	}

	// FUNCTION: LEGO1 0x10034470
	LegoStorage* ReadString(MxString& p_str)
	{
		MxS16 len;
		Read(&len, sizeof(MxS16));

		char* text = new char[len + 1];
		Read(text, len);

		text[len] = '\0';
		p_str = text;
		delete[] text;

		return this;
	}

	// FUNCTION: LEGO1 0x10006030
	LegoStorage* WriteString(MxString p_str)
	{
		const char* data = p_str.GetData();
		LegoU32 fullLength = strlen(data);

		LegoU16 limitedLength = fullLength;
		Write(&limitedLength, sizeof(limitedLength));
		Write((char*) data, (LegoS16) fullLength);

		return this;
	}

	// SYNTHETIC: LEGO1 0x10099230
	// SYNTHETIC: BETA10 0x101846d0
	// LegoFile::`scalar deleting destructor'

protected:
	FILE* m_file; // 0x08
};

#endif // __LEGOSTORAGE_H
