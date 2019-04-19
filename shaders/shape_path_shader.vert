#include "shape_shader_vertex_common"

uniform float uPhaseOffset;
uniform samplerBuffer bOnColors;
uniform samplerBuffer bOffColors;
uniform samplerBuffer bPhasePeriod;

out Vertex
{
	VertexAttrs attrs;
	flat vec4 onColor;
	flat vec4 offColor;
	flat float phase;
	flat float period;
} oVert;

void main() 
{
	oVert.attrs = loadVertexAttrs();

	int shapeIndex = oVert.attrs.shapeIndex;
	oVert.onColor = texelFetch(bOnColors, shapeIndex);
	oVert.offColor = texelFetch(bOffColors, shapeIndex);
	
	vec4 phaseAndPeriod = texelFetch(bPhasePeriod, shapeIndex);
	oVert.phase = phaseAndPeriod.r + uPhaseOffset;
	oVert.period = phaseAndPeriod.g;


	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

#else // TD_PICKING_ACTIVE

	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}


