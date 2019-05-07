#define PANEL_MODE

#include "shape_shader_pixel_common"

uniform sampler2D sPointPositionalTexture;
uniform sampler2D sFaceTexture;

in Vertex
{
	VertexAttrs attrs;
} iVert;

out vec4 fragColor;
void main()
{
	TDCheckDiscard();
	
	vec4 color = vec4(1);

//	vec4 positionalColor = texture(sPointPositionalTexture, iVert.attrs.globalTexCoord.st);
//	color = mix(color, positionalColor, iVert.attrs.globalTexLevel);
//
//	vec4 faceColor = texture(sFaceTexture, iVert.attrs.faceTexCoord.st);
//	color = mix(color, faceColor, iVert.attrs.localTexLevel);
//
//	color *= iVert.attrs.color;

	color = iVert.attrs.color;
	color = applyTexture(color, iVert.attrs, iVert.attrs.texLayer1);
	color = applyTexture(color, iVert.attrs, iVert.attrs.texLayer2);
//	color = applyTexture(color, iVert.attrs, iVert.attrs.texLayer3);
//	color = applyTexture(color, iVert.attrs, iVert.attrs.texLayer4);

	TDAlphaTest(color.a);
	fragColor = TDOutputSwizzle(color);
}

