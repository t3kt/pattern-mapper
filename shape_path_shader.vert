uniform int uShapeCount;
uniform float uPhaseOffset;
uniform samplerBuffer bOnColors;
uniform samplerBuffer bOffColors;
uniform samplerBuffer bAlphas;
uniform samplerBuffer bPhasePeriod;
uniform samplerBuffer bLocalScales;

in int shapeIndex;
in vec3 centerPos;

out Vertex
{
	vec4 color;
	float alpha;
	vec3 worldSpacePos;
	vec2 texCoord0;
	vec2 texCoord1;
	flat int shapeIndex;
	flat vec4 onColor;
	flat vec4 offColor;
	flat float phase;
	flat float period;
} oVert;

void main() 
{

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		oVert.texCoord0.st = texcoord.st;
	}

	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[1]);
		oVert.texCoord1.st = texcoord.st;
	}

	
	//oVert.shapeIndex = shapeIndex;
	float primOffset = oVert.texCoord0.y;
	int shapeIndex = int(primOffset * (uShapeCount-1));
	oVert.shapeIndex = shapeIndex;
	oVert.onColor = texelFetch(bOnColors, shapeIndex);
	oVert.offColor = texelFetch(bOffColors, shapeIndex);
	oVert.alpha = texelFetch(bAlphas, shapeIndex).r;
	
	vec4 phaseAndPeriod = texelFetch(bPhasePeriod, shapeIndex);
	oVert.phase = phaseAndPeriod.r + uPhaseOffset;
	oVert.period = phaseAndPeriod.g;
	vec4 localScale = texelFetch(bLocalScales, shapeIndex);
	
	
	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);
	
	
	worldSpacePos.xyz -= centerPos;
	worldSpacePos.xyz *= localScale.xyz * localScale.w;
	worldSpacePos.xyz += centerPos;
	
	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);
	
	


	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	oVert.worldSpacePos.xyz = worldSpacePos.xyz;
	oVert.color = TDInstanceColor(Cd);

#else // TD_PICKING_ACTIVE

	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}


