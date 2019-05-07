#define PATH_MODE

#include "shape_shader_pixel_common"

uniform float uPhaseOffset;
uniform sampler2D sPointPositionalTexture;

in Vertex
{
	VertexAttrs attrs;
	flat vec4 onColor;
	flat vec4 offColor;
	flat float phase;
	flat float period;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();
	
	float phase = iVert.phase + iVert.attrs.texCoord0.x;
	phase = mod(phase, 1.0);
	phase /= iVert.period;
//	vec4 color = mix(iVert.offColor, iVert.onColor, phase);

	vec4 color = iVert.attrs.color;
	color = applyTexture(color, iVert.attrs, iVert.attrs.pathTex);

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

